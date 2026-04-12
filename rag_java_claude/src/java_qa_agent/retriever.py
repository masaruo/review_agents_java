"""Retrieverモジュール

ChromaDBから類似チャンクを検索し、上位top_k件を返す。
"""

import json
from pathlib import Path

import chromadb

from java_qa_agent.backends.ollama_embed import EmbeddingBackend
from java_qa_agent.schemas.models import ChunkMetadata, JavaChunk, SearchResult


class IndexNotFoundError(Exception):
    """インデックスが存在しないエラー"""

    def __init__(self, project_name: str) -> None:
        self.project_name = project_name
        super().__init__(
            f"プロジェクト '{project_name}' のインデックスが見つかりません。\n"
            f"対処法: make index project={project_name} path=<Javaプロジェクトのパス>"
        )


class Retriever:
    """ChromaDBから類似チャンクを検索するクラス"""

    COLLECTION_NAME = "java_chunks"

    def __init__(
        self,
        embedder: EmbeddingBackend,
        index_base_dir: str = "~/.java_qa_agent/indexes",
    ) -> None:
        """初期化

        Args:
            embedder: エンベディングバックエンド
            index_base_dir: インデックス保存ディレクトリのベースパス
        """
        self.embedder = embedder
        self.index_base_dir = Path(index_base_dir).expanduser()

    def _get_index_dir(self, project_name: str) -> Path:
        """プロジェクトのインデックスディレクトリパスを返す"""
        return self.index_base_dir / project_name

    def retrieve(self, project_name: str, query: str, top_k: int = 5) -> list[SearchResult]:
        """クエリに対して類似チャンクを検索して返す

        Args:
            project_name: プロジェクト名
            query: 検索クエリ（ユーザーの質問文）
            top_k: 取得する最大件数

        Returns:
            SearchResultのリスト（スコア付き）

        Raises:
            IndexNotFoundError: インデックスが存在しない場合
        """
        index_dir = self._get_index_dir(project_name)

        try:
            client = chromadb.PersistentClient(path=str(index_dir))
            collection = client.get_collection(name=self.COLLECTION_NAME)
        except Exception:
            raise IndexNotFoundError(project_name)

        # インデックスが空の場合
        if collection.count() == 0:
            return []

        # クエリをエンベディング
        query_embedding = self.embedder.embed_query(query)

        # 類似度検索
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, collection.count()),
            include=["documents", "metadatas", "distances"],
        )

        # SearchResultに変換
        search_results: list[SearchResult] = []
        if not results["ids"] or not results["ids"][0]:
            return []

        documents = results["documents"][0] if results["documents"] else []
        metadatas = results["metadatas"][0] if results["metadatas"] else []
        distances = results["distances"][0] if results["distances"] else []

        for i, (doc, meta, dist) in enumerate(zip(documents, metadatas, distances)):
            # メタデータを復元
            imports_raw = meta.get("imports", "[]")
            member_vars_raw = meta.get("member_vars", "[]")
            try:
                imports = json.loads(imports_raw) if isinstance(imports_raw, str) else imports_raw
                member_vars = (
                    json.loads(member_vars_raw)
                    if isinstance(member_vars_raw, str)
                    else member_vars_raw
                )
            except (json.JSONDecodeError, TypeError):
                imports = []
                member_vars = []

            chunk_metadata = ChunkMetadata(
                file_path=meta.get("file_path", ""),
                class_name=meta.get("class_name", "Unknown"),
                method_name=meta.get("method_name") or None,
                imports=imports,
                class_signature=meta.get("class_signature", ""),
                member_vars=member_vars,
                chunk_type=meta.get("chunk_type", "method"),
            )

            chunk = JavaChunk(
                content=doc,
                metadata=chunk_metadata,
            )

            # ChromaDBのdistanceをscoreに変換（距離が小さいほど類似度が高い）
            score = 1.0 - float(dist) if dist <= 1.0 else 1.0 / (1.0 + float(dist))

            search_results.append(SearchResult(chunk=chunk, score=score))

        return search_results
