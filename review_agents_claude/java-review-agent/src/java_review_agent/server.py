"""FastAPI サーバー — Web UI + 追加質問API"""

from __future__ import annotations

import asyncio
import uuid
from pathlib import Path
from typing import AsyncGenerator, Literal, Optional

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from java_review_agent.chat import ChatHandler
from java_review_agent.config import load_config
from java_review_agent.graph import build_graph
from java_review_agent.schemas.models import AgentNameType, ReviewInstruction, ScopeType
from java_review_agent.state import initial_state

# ─── セッションストア ──────────────────────────────────────

StatusType = Literal["running", "done", "error"]


class ReviewSession(BaseModel):
    session_id: str
    status: StatusType = "running"
    summary: Optional[str] = None
    file_reports: list[dict[str, str]] = []
    chat_history: list[dict[str, str]] = []
    error: Optional[str] = None


# メモリ上のセッションストア
_sessions: dict[str, ReviewSession] = {}


# ─── リクエスト/レスポンスモデル ───────────────────────────

class ReviewRequest(BaseModel):
    project_dir: str
    scope: ScopeType = "full"
    scope_target: Optional[str] = None
    enabled_agents: list[AgentNameType] = ["bug_detector", "security_scanner"]
    focus_question: Optional[str] = None


class ChatRequest(BaseModel):
    message: str


# ─── FastAPI アプリ ────────────────────────────────────────

app = FastAPI(title="Java Code Review Agent")

# static ディレクトリをマウント（index.html を配信）
_static_dir = Path(__file__).parent.parent.parent / "static"
if _static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")


@app.get("/", response_class=HTMLResponse)
async def root() -> FileResponse:
    """トップページ（index.html）を返す"""
    html_path = _static_dir / "index.html"
    if not html_path.exists():
        raise HTTPException(status_code=404, detail="index.html not found")
    return FileResponse(str(html_path))


# ─── レビューエンドポイント ────────────────────────────────

def _run_review(session_id: str, request: ReviewRequest) -> None:
    """バックグラウンドでレビューを実行する（同期）"""
    session = _sessions[session_id]
    try:
        config = load_config("config.yaml")
        instruction = ReviewInstruction(
            scope=request.scope,
            scope_target=request.scope_target,
            enabled_agents=request.enabled_agents,
            focus_question=request.focus_question,
        )

        app_graph = build_graph(config)
        state = initial_state(
            project_dir=request.project_dir,
            config=config,
            review_instruction=instruction,
        )
        final_state = app_graph.invoke(state)

        if final_state.get("fatal_error"):
            session.status = "error"
            session.error = final_state["fatal_error"]
            return

        # file_reports を {filename, content} 形式に変換
        file_reports = []
        for report in final_state.get("file_reports", []):
            file_reports.append({
                "filename": Path(report.file_path).name,
                "content": report.content,
            })

        session.summary = final_state.get("summary_content") or ""
        session.file_reports = file_reports
        session.status = "done"

    except Exception as exc:
        session.status = "error"
        session.error = str(exc)


@app.post("/review")
async def start_review(
    request: ReviewRequest, background_tasks: BackgroundTasks
) -> dict:
    """レビューをバックグラウンドで開始し、session_id を返す"""
    project_dir = Path(request.project_dir)
    if not project_dir.exists():
        raise HTTPException(
            status_code=400, detail=f"Project directory not found: {request.project_dir}"
        )

    session_id = str(uuid.uuid4())
    _sessions[session_id] = ReviewSession(session_id=session_id)

    # 同期処理をスレッドプールで実行してブロッキングを回避
    loop = asyncio.get_event_loop()
    background_tasks.add_task(
        loop.run_in_executor, None, _run_review, session_id, request
    )

    return {"session_id": session_id, "status": "running"}


@app.get("/review/{session_id}")
async def get_review(session_id: str) -> dict:
    """レビュー結果を取得する"""
    session = _sessions.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "session_id": session.session_id,
        "status": session.status,
        "summary": session.summary,
        "file_reports": session.file_reports,
        "error": session.error,
    }


# ─── チャットエンドポイント ────────────────────────────────

@app.post("/chat/{session_id}")
async def chat(session_id: str, request: ChatRequest) -> EventSourceResponse:
    """レビュー結果をコンテキストに追加質問する（SSEストリーミング）"""
    session = _sessions.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status != "done":
        raise HTTPException(status_code=400, detail="Review is not completed yet")

    # レビュー結果をコンテキストとして結合
    review_context = _build_review_context(session)

    config = load_config("config.yaml")
    handler = ChatHandler(
        base_url=config.ollama.base_url,
        model=config.ollama.model,
        review_context=review_context,
    )

    # 現在の履歴を保存（ストリーム完了後に追記するためコピー）
    history_snapshot = list(session.chat_history)
    message = request.message

    async def event_generator() -> AsyncGenerator[dict, None]:
        full_response = []
        loop = asyncio.get_event_loop()

        def _stream_sync() -> list[str]:
            return list(handler.stream(message, history_snapshot))

        chunks = await loop.run_in_executor(None, _stream_sync)

        for chunk in chunks:
            full_response.append(chunk)
            yield {"data": f'{{"delta": {_json_str(chunk)}}}'}

        # 会話履歴を更新
        session.chat_history.append({"role": "user", "content": message})
        session.chat_history.append({"role": "assistant", "content": "".join(full_response)})

        yield {"data": "[DONE]"}

    return EventSourceResponse(event_generator())


def _build_review_context(session: ReviewSession) -> str:
    """サマリー + ファイルレポートを結合してコンテキスト文字列を作る"""
    parts: list[str] = []
    if session.summary:
        parts.append(f"### 全体サマリー\n\n{session.summary}")
    for report in session.file_reports:
        parts.append(f"### {report['filename']}\n\n{report['content']}")
    return "\n\n---\n\n".join(parts)


def _json_str(s: str) -> str:
    """文字列をJSONの文字列値として安全にエンコードする"""
    import json
    return json.dumps(s, ensure_ascii=False)
