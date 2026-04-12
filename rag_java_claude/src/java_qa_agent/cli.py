"""CLI エントリポイント

typer を使用した CLI アプリケーション。
4つのサブコマンドを提供する: index, chat, list, delete
"""

import sys
from pathlib import Path
from typing import Annotated

import typer

from java_qa_agent.backends.ollama_embed import OllamaEmbedding
from java_qa_agent.backends.ollama_llm import OllamaLLM
from java_qa_agent.chat_session import ChatSession
from java_qa_agent.config import get_config
from java_qa_agent.indexer import Indexer
from java_qa_agent.logger import SessionLogger
from java_qa_agent.project_manager import ProjectManager, ProjectNotFoundError
from java_qa_agent.retriever import IndexNotFoundError, Retriever

app = typer.Typer(
    name="java-qa",
    help="Java Code Q&A RAG Agent - Javaプロジェクトのコードに関する質問に答えます",
    add_completion=False,
)


def _check_ollama_and_exit(
    llm: OllamaLLM,
    embedder: OllamaEmbedding,
    config_obj: object,
) -> None:
    """Ollama接続とモデル存在を確認し、失敗した場合は即時終了する"""
    from java_qa_agent.schemas.models import AppConfig

    cfg = config_obj if isinstance(config_obj, AppConfig) else get_config()

    # 接続確認
    if not llm.check_connection():
        print(
            f"エラー: Ollamaサーバーに接続できません\n"
            f"エンドポイント: {cfg.ollama.base_url}\n"
            f"対処法:\n"
            f"  1. ollama serve コマンドでOllamaを起動してください\n"
            f"  2. または OLLAMA_BASE_URL 環境変数で正しいエンドポイントを設定してください",
            file=sys.stderr,
        )
        raise typer.Exit(code=1)

    # 推論モデル確認
    if not llm.check_model_available(cfg.ollama.model):
        print(
            f"エラー: モデルが見つかりません: {cfg.ollama.model}\n"
            f"対処法: 以下のコマンドでモデルを取得してください:\n"
            f"  ollama pull {cfg.ollama.model}",
            file=sys.stderr,
        )
        raise typer.Exit(code=1)

    # エンベディングモデル確認
    if not embedder.check_model_available(cfg.ollama.embed_model):
        print(
            f"エラー: エンベディングモデルが見つかりません: {cfg.ollama.embed_model}\n"
            f"対処法: 以下のコマンドでモデルを取得してください:\n"
            f"  ollama pull {cfg.ollama.embed_model}",
            file=sys.stderr,
        )
        raise typer.Exit(code=1)


@app.command()
def index(
    project: Annotated[str, typer.Option("--project", "-p", help="プロジェクト名")],
    path: Annotated[
        str, typer.Option("--path", "-d", help="Javaプロジェクトのルートディレクトリパス")
    ],
) -> None:
    """プロジェクトのインデックスを構築（または再構築）する"""
    config = get_config()

    # ディレクトリ存在確認
    project_path = Path(path)
    if not project_path.exists():
        print(f"エラー: ディレクトリが見つかりません: {path}", file=sys.stderr)
        raise typer.Exit(code=1)

    # バックエンドの初期化
    llm = OllamaLLM(
        base_url=config.ollama.base_url,
        model=config.ollama.model,
        timeout_seconds=config.ollama.timeout_seconds,
    )
    embedder = OllamaEmbedding(
        base_url=config.ollama.base_url,
        model=config.ollama.embed_model,
        timeout_seconds=config.ollama.timeout_seconds,
    )

    # Ollama接続・モデル確認
    _check_ollama_and_exit(llm, embedder, config)

    # プロジェクト登録
    project_manager = ProjectManager(
        base_dir=str(Path(config.storage.index_dir).parent.expanduser())
    )
    project_manager.register(project, str(project_path.resolve()))

    # インデックス構築
    indexer = Indexer(
        embedder=embedder,
        index_base_dir=config.storage.index_dir,
        token_threshold=config.rag.chunk_token_threshold,
    )

    print(f"プロジェクト '{project}' のインデックスを構築中...")
    scan_dir = str(project_path / "src") if (project_path / "src").exists() else str(project_path)
    print(f"スキャン対象: {scan_dir}")

    count = indexer.build_index(project, str(project_path.resolve()))

    if count == 0:
        print(f"警告: .javaファイルが見つかりませんでした: {scan_dir}")
    else:
        print(f"インデックス構築完了: {count}チャンクを保存しました")


@app.command()
def chat(
    project: Annotated[str, typer.Option("--project", "-p", help="プロジェクト名")],
) -> None:
    """プロジェクトの対話セッションを開始する"""
    config = get_config()

    # プロジェクト存在確認
    project_manager = ProjectManager(
        base_dir=str(Path(config.storage.index_dir).parent.expanduser())
    )
    try:
        project_info = project_manager.get(project)
    except ProjectNotFoundError as e:
        print(str(e), file=sys.stderr)
        raise typer.Exit(code=1)

    # バックエンドの初期化
    llm = OllamaLLM(
        base_url=config.ollama.base_url,
        model=config.ollama.model,
        timeout_seconds=config.ollama.timeout_seconds,
    )
    embedder = OllamaEmbedding(
        base_url=config.ollama.base_url,
        model=config.ollama.embed_model,
        timeout_seconds=config.ollama.timeout_seconds,
    )

    # Ollama接続・モデル確認
    _check_ollama_and_exit(llm, embedder, config)

    # Retrieverの初期化とインデックス存在確認
    retriever = Retriever(
        embedder=embedder,
        index_base_dir=config.storage.index_dir,
    )

    # インデックス存在確認（ダミーでretrieveして確認）
    try:
        retriever.retrieve(project, "test", top_k=1)
    except IndexNotFoundError:
        print(
            f"エラー: プロジェクト '{project}' のインデックスが見つかりません\n"
            f"対処法: 以下のコマンドでインデックスを構築してください:\n"
            f"  make index project={project} path={project_info.path}\n"
            f"  または: java-qa index --project {project} --path {project_info.path}",
            file=sys.stderr,
        )
        raise typer.Exit(code=1)

    # ロガーの初期化
    logger = SessionLogger(
        project_name=project,
        log_base_dir=config.storage.log_dir,
        save_logs=config.storage.save_logs,
    )

    # チャットセッションの開始
    session = ChatSession(
        project_name=project,
        config=config,
        llm=llm,
        retriever=retriever,
        logger=logger,
    )
    session.start()


@app.command(name="list")
def list_projects() -> None:
    """登録済みプロジェクトの一覧を表示する"""
    config = get_config()
    project_manager = ProjectManager(
        base_dir=str(Path(config.storage.index_dir).parent.expanduser())
    )
    projects = project_manager.list_projects()

    if not projects:
        print("登録済みプロジェクトはありません")
        print("java-qa index --project <name> --path <dir> でプロジェクトを登録してください")
        return

    print("登録済みプロジェクト:")
    for proj in projects:
        updated = proj.updated_at.strftime("%Y-%m-%d %H:%M:%S")
        print(f"  {proj.name:<20} {proj.path:<50} {updated}")


@app.command()
def delete(
    project: Annotated[str, typer.Option("--project", "-p", help="プロジェクト名")],
) -> None:
    """プロジェクトのインデックスを削除する"""
    config = get_config()
    project_manager = ProjectManager(
        base_dir=str(Path(config.storage.index_dir).parent.expanduser())
    )

    # プロジェクト存在確認
    try:
        project_manager.get(project)
    except ProjectNotFoundError as e:
        print(str(e), file=sys.stderr)
        raise typer.Exit(code=1)

    # 確認プロンプト
    confirmed = typer.confirm(f"プロジェクト '{project}' を削除しますか？")
    if not confirmed:
        print("削除をキャンセルしました")
        return

    project_manager.delete(project)
    print(f"プロジェクト '{project}' を削除しました")


if __name__ == "__main__":
    app()
