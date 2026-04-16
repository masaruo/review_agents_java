"""Pydantic v2 モデル定義 — 全スキーマ"""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional, TypedDict

from pydantic import BaseModel, Field


# ─────────────────────────────────────────────
# 型エイリアス
# ─────────────────────────────────────────────

SeverityType = Literal["critical", "major", "minor", "info"]
CategoryType = Literal["bug", "security", "efficiency", "design", "style"]
SkipReasonType = Literal["Resource Limit", "Parse Error", "Connection Error"]
ScopeType = Literal["full", "file", "class", "function"]
AgentNameType = Literal[
    "bug_detector",
    "security_scanner",
    "efficiency_analyzer",
    "design_critic",
    "style_reviewer",
]

DEFAULT_AGENTS: list[AgentNameType] = ["bug_detector", "security_scanner"]


# ─────────────────────────────────────────────
# インタラクティブ指示モデル
# ─────────────────────────────────────────────


class ReviewInstruction(BaseModel):
    scope: ScopeType = "full"
    scope_target: Optional[str] = None
    """scope が "file"/"class"/"function" のとき有効。部分一致フィルタ。"""
    enabled_agents: list[AgentNameType] = Field(
        default_factory=lambda: list(DEFAULT_AGENTS)
    )
    """実行するエージェント名一覧"""
    focus_question: Optional[str] = None
    """Summary Generator のプロンプトに追記されるフリーテキスト質問"""


# ─────────────────────────────────────────────
# 設定モデル
# ─────────────────────────────────────────────


class OllamaConfig(BaseModel):
    base_url: str = "http://localhost:11434"
    model: str = "qwen2.5-coder:7b"
    timeout_seconds: int = 120


class ProcessingConfig(BaseModel):
    max_concurrency: int = Field(default=1, ge=1)
    chunk_token_threshold: int = Field(default=1000, ge=100)
    max_input_tokens: int = Field(default=3000, ge=500)
    response_reserve_tokens: int = Field(default=1000, ge=100)


class OutputConfig(BaseModel):
    dir: str = "./review_output"


class Config(BaseModel):
    java_version: int = 17
    ollama: OllamaConfig = Field(default_factory=OllamaConfig)
    processing: ProcessingConfig = Field(default_factory=ProcessingConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)


# ─────────────────────────────────────────────
# コードスロットモデル
# ─────────────────────────────────────────────


class CodeSlot(BaseModel):
    slot_id: str
    """"{file_path}::{method_name}" または "{file_path}::whole" の形式"""
    file_path: str
    method_name: str
    """メソッド名。ファイル全体の場合は "whole"。"""
    content: str
    """レビュー対象コード（コンテキスト付与済み）"""
    is_truncated: bool = False
    """max_input_tokens で切り詰めが発生した場合 True"""


# ─────────────────────────────────────────────
# レビュー問題モデル
# ─────────────────────────────────────────────


class ReviewIssue(BaseModel):
    priority: int = Field(ge=1, le=5)
    """1=バグ / 2=セキュリティ / 3=効率性 / 4=設計 / 5=可読性"""
    category: CategoryType
    severity: SeverityType
    location: str
    """例: "ClassName#methodName" または行番号情報"""
    description: str
    suggestion: str


# ─────────────────────────────────────────────
# エージェント出力モデル
# ─────────────────────────────────────────────


class AgentOutput(BaseModel):
    slot_id: str
    agent_name: str
    issues: list[ReviewIssue] = Field(default_factory=list)
    skipped: bool = False
    skip_reason: Optional[str] = None


# ─────────────────────────────────────────────
# スキップ記録モデル
# ─────────────────────────────────────────────


class SkippedItem(BaseModel):
    target: str
    """slot_id または file_path"""
    agent_name: str
    reason: SkipReasonType
    detail: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ─────────────────────────────────────────────
# 集約結果モデル
# ─────────────────────────────────────────────


class AggregatedResult(BaseModel):
    file_path: str
    issues: list[ReviewIssue] = Field(default_factory=list)
    """優先度昇順・重複除去済み"""
    skipped_items: list[SkippedItem] = Field(default_factory=list)


# ─────────────────────────────────────────────
# ファイルレポートモデル
# ─────────────────────────────────────────────


class FileReport(BaseModel):
    file_path: str
    report_path: str
    content: str
    issue_count: int


# ─────────────────────────────────────────────
# LLM レスポンスパースモデル
# ─────────────────────────────────────────────


class LLMReviewResponse(BaseModel):
    issues: list[ReviewIssue] = Field(default_factory=list)


# ─────────────────────────────────────────────
# LangGraph グラフ状態
# ─────────────────────────────────────────────


class ReviewGraphState(TypedDict, total=False):
    # 入力・設定
    project_dir: str
    java_version: int
    config: Config
    review_instruction: ReviewInstruction

    # FileScanner 結果
    java_files: list[str]
    current_file_index: int

    # Preprocessor 結果
    current_file_path: str
    slots: list[CodeSlot]
    current_slot_index: int

    # レビューエージェント結果（スロットごとに累積）
    slot_agent_outputs: list[AgentOutput]

    # Aggregator 結果
    aggregated_result: Optional[AggregatedResult]

    # File Report Generator 結果
    file_reports: list[FileReport]

    # スキップ一覧（全ファイル横断）
    skipped_items: list[SkippedItem]

    # Summary Generator 結果
    summary_content: Optional[str]

    # 致命的エラー（即時終了用）
    fatal_error: Optional[str]
