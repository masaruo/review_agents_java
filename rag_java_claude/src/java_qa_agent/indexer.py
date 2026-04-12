"""インデックス構築モジュール

FileScanner: .javaファイルの再帰スキャン
JavaChunker: Javaソースのメソッド単位分割とメタデータ付与
Indexer: スキャン→チャンキング→エンベディング→ChromaDB保存を統括
"""

import json
import re
import uuid
from pathlib import Path

import chromadb
import tiktoken

from java_qa_agent.backends.ollama_embed import EmbeddingBackend
from java_qa_agent.schemas.models import ChunkMetadata, JavaChunk


class FileScanner:
    """ディレクトリを再帰的にスキャンして.javaファイルを収集する"""

    def scan(self, root_dir: str) -> list[str]:
        """ディレクトリを再帰的にスキャンして.javaファイルを返す

        Args:
            root_dir: スキャンするルートディレクトリ

        Returns:
            .javaファイルの絶対パスリスト

        Raises:
            FileNotFoundError: root_dirが存在しない場合
        """
        path = Path(root_dir)
        if not path.exists():
            raise FileNotFoundError(f"ディレクトリが見つかりません: {root_dir}")

        java_files = [str(f.resolve()) for f in path.rglob("*.java")]
        return sorted(java_files)


class JavaChunker:
    """Javaソースファイルをメソッド単位に分割し、メタデータを付与する

    正規表現ベースのパーサーを使用する（JavaのASTライブラリは不要）。
    """

    # インポート文のパターン
    IMPORT_PATTERN = re.compile(r"^import\s+[\w.]+;", re.MULTILINE)

    # クラスシグネチャのパターン（行頭から始まる宣言のみマッチ）
    CLASS_PATTERN = re.compile(
        r"^\s*(?:(public|private|protected)\s+)?(?:(abstract|final)\s+)*class\s+(\w+)"
        r"(?:\s+extends\s+\w+)?(?:\s+implements\s+[\w,\s<>]+)?",
        re.MULTILINE,
    )

    # メンバー変数のパターン（クラスレベルのフィールド）
    MEMBER_VAR_PATTERN = re.compile(
        r"^\s+(private|protected|public)\s+(?:final\s+)?[\w<>\[\]]+\s+\w+\s*[;=]",
        re.MULTILINE,
    )

    # メソッドのパターン
    METHOD_PATTERN = re.compile(
        r"(?:(?:public|private|protected|static|final|synchronized|abstract)\s+)+"
        r"(?:[\w<>\[\]]+)\s+(\w+)\s*\([^)]*\)\s*(?:throws\s+[\w,\s]+)?\s*\{",
        re.MULTILINE,
    )

    def __init__(self, token_threshold: int = 1000) -> None:
        """初期化

        Args:
            token_threshold: このトークン数未満はファイル全体を1チャンクとして扱う
        """
        self.token_threshold = token_threshold
        self._encoding = tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, text: str) -> int:
        """テキストのトークン数を計算する

        Args:
            text: 計算対象のテキスト

        Returns:
            トークン数
        """
        return len(self._encoding.encode(text))

    def extract_imports(self, source: str) -> list[str]:
        """ソースからインポート文を抽出する

        Args:
            source: Javaソースコード

        Returns:
            インポート文のリスト
        """
        return self.IMPORT_PATTERN.findall(source)

    def extract_class_signature(self, source: str) -> str:
        """ソースからクラスシグネチャを抽出する

        Args:
            source: Javaソースコード

        Returns:
            クラスシグネチャ文字列（見つからない場合は空文字列）
        """
        match = self.CLASS_PATTERN.search(source)
        if match:
            return match.group(0).strip()
        return ""

    def extract_class_name(self, source: str) -> str:
        """ソースからクラス名を抽出する

        Args:
            source: Javaソースコード

        Returns:
            クラス名（見つからない場合は"Unknown"）
        """
        match = self.CLASS_PATTERN.search(source)
        if match:
            return match.group(3)
        return "Unknown"

    def extract_member_vars(self, source: str) -> list[str]:
        """ソースからメンバー変数を抽出する

        Args:
            source: Javaソースコード

        Returns:
            メンバー変数宣言のリスト
        """
        result = []
        for match in self.MEMBER_VAR_PATTERN.finditer(source):
            result.append(match.group(0).strip())
        return result

    def _extract_methods(self, source: str) -> list[tuple[str, int, int]]:
        """ソースからメソッドを抽出する（名前、開始位置、終了位置）

        Args:
            source: Javaソースコード

        Returns:
            (メソッド名, 開始位置, 終了位置) のリスト
        """
        methods: list[tuple[str, int, int]] = []

        for match in self.METHOD_PATTERN.finditer(source):
            method_name = match.group(1)
            start = match.start()

            # コンストラクタやキーワードを除外
            if method_name in ("if", "while", "for", "switch", "catch", "try", "else"):
                continue

            # 対応する閉じ括弧を探す
            brace_count = 0
            end = start
            found_open = False
            for i in range(match.start(), len(source)):
                if source[i] == "{":
                    brace_count += 1
                    found_open = True
                elif source[i] == "}":
                    brace_count -= 1
                    if found_open and brace_count == 0:
                        end = i + 1
                        break

            if end > start:
                methods.append((method_name, start, end))

        return methods

    def chunk_file(self, file_path: str) -> list[JavaChunk]:
        """Javaファイルをチャンク化する

        Args:
            file_path: Javaファイルの絶対パス

        Returns:
            JavaChunkのリスト

        Raises:
            IOError: ファイルが読み込めない場合
        """
        try:
            with open(file_path, encoding="utf-8") as f:
                source = f.read()
        except OSError as e:
            raise OSError(f"ファイルが読み込めません: {file_path}") from e

        # メタデータを抽出
        imports = self.extract_imports(source)
        class_signature = self.extract_class_signature(source)
        class_name = self.extract_class_name(source)
        member_vars = self.extract_member_vars(source)

        token_count = self.count_tokens(source)

        # トークン数がしきい値未満の場合はファイル全体を1チャンクとして返す
        if token_count < self.token_threshold:
            metadata = ChunkMetadata(
                file_path=file_path,
                class_name=class_name,
                method_name=None,
                imports=imports,
                class_signature=class_signature,
                member_vars=member_vars,
                chunk_type="file",
            )
            return [
                JavaChunk(
                    content=source,
                    metadata=metadata,
                    token_count=token_count,
                )
            ]

        # メソッド単位に分割する
        methods = self._extract_methods(source)

        if not methods:
            # メソッドが見つからない場合はファイル全体を返す
            metadata = ChunkMetadata(
                file_path=file_path,
                class_name=class_name,
                method_name=None,
                imports=imports,
                class_signature=class_signature,
                member_vars=member_vars,
                chunk_type="file",
            )
            return [
                JavaChunk(
                    content=source,
                    metadata=metadata,
                    token_count=token_count,
                )
            ]

        chunks: list[JavaChunk] = []
        for method_name, start, end in methods:
            method_content = source[start:end]
            method_token_count = self.count_tokens(method_content)

            metadata = ChunkMetadata(
                file_path=file_path,
                class_name=class_name,
                method_name=method_name,
                imports=imports,
                class_signature=class_signature,
                member_vars=member_vars,
                chunk_type="method",
            )
            chunks.append(
                JavaChunk(
                    content=method_content,
                    metadata=metadata,
                    token_count=method_token_count,
                )
            )

        return chunks


class Indexer:
    """インデックス構築を統括するクラス

    FileScanner → JavaChunker → OllamaEmbedding → ChromaDB の一連のフローを実行する。
    """

    COLLECTION_NAME = "java_chunks"

    def __init__(
        self,
        embedder: EmbeddingBackend,
        index_base_dir: str = "~/.java_qa_agent/indexes",
        token_threshold: int = 1000,
    ) -> None:
        """初期化

        Args:
            embedder: エンベディングバックエンド
            index_base_dir: インデックス保存ディレクトリのベースパス
            token_threshold: チャンキングのトークンしきい値
        """
        self.embedder = embedder
        self.index_base_dir = Path(index_base_dir).expanduser()
        self.scanner = FileScanner()
        self.chunker = JavaChunker(token_threshold=token_threshold)

    def _get_index_dir(self, project_name: str) -> Path:
        """プロジェクトのインデックスディレクトリパスを返す"""
        return self.index_base_dir / project_name

    def build_index(self, project_name: str, project_path: str) -> int:
        """インデックスを構築する（全件再構築）

        Args:
            project_name: プロジェクト名（ChromaDBコレクション識別子）
            project_path: Javaプロジェクトのルートディレクトリ

        Returns:
            インデックスされたチャンク数
        """
        # スキャン対象ディレクトリを決定（src/があればsrc/を優先）
        root_path = Path(project_path)
        src_path = root_path / "src"
        scan_dir = str(src_path) if src_path.exists() else str(root_path)

        # .javaファイルをスキャン
        java_files = self.scanner.scan(scan_dir)

        if not java_files:
            print(f"警告: .javaファイルが見つかりませんでした: {scan_dir}", flush=True)
            return 0

        # チャンク化
        all_chunks: list[JavaChunk] = []
        for java_file in java_files:
            try:
                chunks = self.chunker.chunk_file(java_file)
                all_chunks.extend(chunks)
            except OSError as e:
                print(f"警告: ファイルのチャンク化に失敗しました: {e}", flush=True)
                continue

        if not all_chunks:
            return 0

        # バッチエンベディング
        texts = [chunk.content for chunk in all_chunks]
        embeddings = self.embedder.embed(texts)

        # ChromaDBに保存
        index_dir = self._get_index_dir(project_name)
        index_dir.mkdir(parents=True, exist_ok=True)

        client = chromadb.PersistentClient(path=str(index_dir))
        collection = client.get_or_create_collection(name=self.COLLECTION_NAME)

        # 既存データを全削除
        existing_count = collection.count()
        if existing_count > 0:
            all_ids = collection.get()["ids"]
            if all_ids:
                collection.delete(ids=all_ids)

        # 新しいデータを挿入
        ids = [str(uuid.uuid4()) for _ in all_chunks]
        documents = [chunk.content for chunk in all_chunks]
        metadatas = [
            {
                "file_path": chunk.metadata.file_path,
                "class_name": chunk.metadata.class_name,
                "method_name": chunk.metadata.method_name or "",
                "imports": json.dumps(chunk.metadata.imports),
                "class_signature": chunk.metadata.class_signature,
                "member_vars": json.dumps(chunk.metadata.member_vars),
                "chunk_type": chunk.metadata.chunk_type,
            }
            for chunk in all_chunks
        ]

        collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )

        return len(all_chunks)
