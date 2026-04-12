"""Java Q&A RAG Agent 使用例

このスクリプトは Python API を直接使用してRAGパイプラインを実行する例です。
通常はCLI（java-qaコマンド）またはMakefileを使用してください。

使い方:
    uv run python examples/qa_sample.py
"""

import sys
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from java_qa_agent.backends.ollama_embed import OllamaEmbedding
from java_qa_agent.backends.ollama_llm import OllamaLLM
from java_qa_agent.chat_session import ChatSession
from java_qa_agent.config import get_config
from java_qa_agent.indexer import Indexer
from java_qa_agent.logger import SessionLogger
from java_qa_agent.retriever import IndexNotFoundError, Retriever


def main() -> None:
    """メイン関数 - RAGパイプラインの使用例"""
    config = get_config()

    print("=== Java Q&A RAG Agent 使用例 ===")
    print()

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

    # 接続確認
    print("Ollama接続確認中...")
    if not llm.check_connection():
        print("エラー: Ollamaサーバーに接続できません", file=sys.stderr)
        print("ollama serve コマンドでOllamaを起動してください", file=sys.stderr)
        return

    print("接続成功！")
    print()

    # フィクスチャディレクトリを使用した例
    fixtures_dir = Path(__file__).parent.parent / "tests" / "fixtures" / "sample_java"
    project_name = "sample-project"

    # インデックス構築
    print(f"インデックス構築中: {fixtures_dir}")
    indexer = Indexer(
        embedder=embedder,
        index_base_dir=config.storage.index_dir,
        token_threshold=config.rag.chunk_token_threshold,
    )

    # フィクスチャのsample_javaをsrcとして扱うためparentを指定
    count = indexer.build_index(project_name, str(fixtures_dir.parent))
    print(f"インデックス構築完了: {count}チャンク")
    print()

    # 検索テスト
    print("検索テスト: 'addメソッドを教えてください'")
    retriever = Retriever(
        embedder=embedder,
        index_base_dir=config.storage.index_dir,
    )

    try:
        results = retriever.retrieve(project_name, "addメソッドを教えてください", top_k=3)
        print(f"検索結果: {len(results)}件")
        for result in results:
            print(f"  - {result.chunk.metadata.class_name}.{result.chunk.metadata.method_name} "
                  f"(スコア: {result.score:.3f})")
    except IndexNotFoundError as e:
        print(f"エラー: {e}", file=sys.stderr)
        return

    print()
    print("対話セッションを開始します（Ctrl+Cで終了）")
    print()

    # チャットセッション
    logger = SessionLogger(
        project_name=project_name,
        log_base_dir=config.storage.log_dir,
        save_logs=False,  # サンプルではログ保存を無効化
    )

    session = ChatSession(
        project_name=project_name,
        config=config,
        llm=llm,
        retriever=retriever,
        logger=logger,
    )
    session.start()


if __name__ == "__main__":
    main()
