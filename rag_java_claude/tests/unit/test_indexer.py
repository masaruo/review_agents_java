"""FileScanner と Indexer のユニットテスト"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from java_qa_agent.indexer import FileScanner, Indexer
from java_qa_agent.schemas.models import ChunkMetadata, JavaChunk

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "sample_java"


class TestFileScanner:
    def test_scan_returns_only_java_files(self, tmp_path: Path) -> None:
        """.javaファイルのみを返すことを確認する"""
        (tmp_path / "Main.java").write_text("public class Main {}")
        (tmp_path / "README.md").write_text("# README")
        (tmp_path / "config.xml").write_text("<config/>")

        scanner = FileScanner()
        files = scanner.scan(str(tmp_path))
        assert len(files) == 1
        assert files[0].endswith("Main.java")

    def test_scan_recursive(self, tmp_path: Path) -> None:
        """サブディレクトリも再帰的にスキャンすることを確認する"""
        sub_dir = tmp_path / "com" / "example"
        sub_dir.mkdir(parents=True)
        (tmp_path / "Root.java").write_text("public class Root {}")
        (sub_dir / "Sub.java").write_text("public class Sub {}")

        scanner = FileScanner()
        files = scanner.scan(str(tmp_path))
        assert len(files) == 2
        file_names = [Path(f).name for f in files]
        assert "Root.java" in file_names
        assert "Sub.java" in file_names

    def test_scan_empty_directory(self, tmp_path: Path) -> None:
        """空ディレクトリで空リストを返すことを確認する"""
        scanner = FileScanner()
        files = scanner.scan(str(tmp_path))
        assert files == []

    def test_scan_nonexistent_directory(self) -> None:
        """存在しないディレクトリでFileNotFoundErrorを発生させることを確認する"""
        scanner = FileScanner()
        with pytest.raises(FileNotFoundError):
            scanner.scan("/nonexistent/path/to/dir")

    def test_scan_no_java_files(self, tmp_path: Path) -> None:
        """.javaファイルがない場合に空リストを返すことを確認する"""
        (tmp_path / "README.md").write_text("# README")
        (tmp_path / "config.xml").write_text("<config/>")

        scanner = FileScanner()
        files = scanner.scan(str(tmp_path))
        assert files == []

    def test_scan_fixture_directory(self) -> None:
        """フィクスチャディレクトリをスキャンできることを確認する"""
        scanner = FileScanner()
        files = scanner.scan(str(FIXTURES_DIR))
        assert len(files) == 2
        file_names = [Path(f).name for f in files]
        assert "Calculator.java" in file_names
        assert "UserService.java" in file_names


class TestIndexer:
    def _make_mock_chunk(self, class_name: str = "Test", method_name: str = "method") -> JavaChunk:
        """テスト用のモックチャンクを生成する"""
        return JavaChunk(
            content=f"public void {method_name}() {{}}",
            metadata=ChunkMetadata(
                file_path=f"/path/to/{class_name}.java",
                class_name=class_name,
                method_name=method_name,
            ),
            token_count=10,
        )

    def test_indexer_calls_embedder_with_batch(self, tmp_path: Path) -> None:
        """エンベディングがバッチで呼ばれることを確認する"""
        mock_embedder = MagicMock()
        mock_embedder.embed.return_value = [[0.1, 0.2, 0.3]] * 3
        mock_collection = MagicMock()
        mock_collection.count.return_value = 0

        mock_client = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection

        # src/ディレクトリを作成してJavaファイルを配置
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "Main.java").write_text(
            "public class Main {"
            " public void run() {} public void stop() {} public void pause() {} }"
        )

        with patch("chromadb.PersistentClient", return_value=mock_client):
            indexer = Indexer(
                embedder=mock_embedder,
                index_base_dir=str(tmp_path / ".indexes"),
            )
            indexer.build_index("test-project", str(tmp_path))

        # embedが呼ばれたことを確認
        mock_embedder.embed.assert_called_once()
        # 引数がリストであることを確認
        call_args = mock_embedder.embed.call_args[0][0]
        assert isinstance(call_args, list)

    def test_indexer_full_rebuild_deletes_first(self, tmp_path: Path) -> None:
        """既存コレクションを全削除してから挿入することを確認する"""
        mock_embedder = MagicMock()
        mock_embedder.embed.return_value = [[0.1, 0.2, 0.3]]
        mock_collection = MagicMock()
        mock_collection.count.return_value = 5  # 既存の5件

        mock_client = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection

        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "Main.java").write_text("public class Main { public void run() {} }")

        with patch("chromadb.PersistentClient", return_value=mock_client):
            indexer = Indexer(
                embedder=mock_embedder,
                index_base_dir=str(tmp_path / ".indexes"),
            )
            indexer.build_index("test-project", str(tmp_path))

        # deleteが呼ばれたことを確認
        mock_collection.delete.assert_called()

    def test_indexer_returns_chunk_count(self, tmp_path: Path) -> None:
        """インデックスされたチャンク数を返すことを確認する"""
        mock_embedder = MagicMock()
        mock_embedder.embed.return_value = [[0.1, 0.2, 0.3]]
        mock_collection = MagicMock()
        mock_collection.count.return_value = 0

        mock_client = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection

        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "Main.java").write_text("public class Main { public void run() {} }")

        with patch("chromadb.PersistentClient", return_value=mock_client):
            indexer = Indexer(
                embedder=mock_embedder,
                index_base_dir=str(tmp_path / ".indexes"),
            )
            count = indexer.build_index("test-project", str(tmp_path))

        assert isinstance(count, int)
        assert count >= 0

    def test_indexer_empty_project(self, tmp_path: Path) -> None:
        """.javaファイルが0件の場合に0を返すことを確認する"""
        mock_embedder = MagicMock()
        mock_collection = MagicMock()
        mock_client = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection

        src_dir = tmp_path / "src"
        src_dir.mkdir()
        # Javaファイルなし

        with patch("chromadb.PersistentClient", return_value=mock_client):
            indexer = Indexer(
                embedder=mock_embedder,
                index_base_dir=str(tmp_path / ".indexes"),
            )
            count = indexer.build_index("test-project", str(tmp_path))

        assert count == 0
        mock_embedder.embed.assert_not_called()

    def test_indexer_no_src_directory(self, tmp_path: Path) -> None:
        """srcディレクトリがない場合も動作することを確認する"""
        mock_embedder = MagicMock()
        mock_collection = MagicMock()
        mock_collection.count.return_value = 0
        mock_client = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection

        # src/ディレクトリを作らずにJavaファイルを直接配置
        (tmp_path / "Main.java").write_text("public class Main { public void run() {} }")

        with patch("chromadb.PersistentClient", return_value=mock_client):
            indexer = Indexer(
                embedder=mock_embedder,
                index_base_dir=str(tmp_path / ".indexes"),
            )
            # src/がない場合はrootディレクトリをスキャン
            count = indexer.build_index("test-project", str(tmp_path))

        assert count >= 0
