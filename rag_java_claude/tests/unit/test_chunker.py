"""JavaChunkerのユニットテスト"""

from pathlib import Path

from java_qa_agent.indexer import JavaChunker

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "sample_java"
CALCULATOR_PATH = str(FIXTURES_DIR / "Calculator.java")
USER_SERVICE_PATH = str(FIXTURES_DIR / "UserService.java")


class TestImportExtraction:
    def test_extract_imports_from_calculator(self) -> None:
        """Calculator.javaからインポートを正しく抽出できることを確認する"""
        chunker = JavaChunker()
        with open(CALCULATOR_PATH) as f:
            source = f.read()
        imports = chunker.extract_imports(source)
        assert "import java.util.List;" in imports
        assert "import java.util.ArrayList;" in imports
        assert len(imports) == 2

    def test_extract_imports_from_user_service(self) -> None:
        """UserService.javaからインポートを正しく抽出できることを確認する"""
        chunker = JavaChunker()
        with open(USER_SERVICE_PATH) as f:
            source = f.read()
        imports = chunker.extract_imports(source)
        assert len(imports) > 0
        assert any("UserRepository" in imp for imp in imports)

    def test_extract_imports_empty(self) -> None:
        """インポートなしのJavaで空リストを返すことを確認する"""
        chunker = JavaChunker()
        source = "public class Hello { public static void main(String[] args) {} }"
        imports = chunker.extract_imports(source)
        assert imports == []


class TestClassSignatureExtraction:
    def test_extract_class_signature_public(self) -> None:
        """publicクラスのシグネチャを正しく抽出できることを確認する"""
        chunker = JavaChunker()
        with open(CALCULATOR_PATH) as f:
            source = f.read()
        signature = chunker.extract_class_signature(source)
        assert "Calculator" in signature
        assert "class" in signature

    def test_extract_class_signature_with_implements(self) -> None:
        """implementsを含むシグネチャを抽出できることを確認する"""
        chunker = JavaChunker()
        source = "public class MyService implements Runnable { }"
        signature = chunker.extract_class_signature(source)
        assert "MyService" in signature

    def test_extract_class_name_from_signature(self) -> None:
        """クラス名がシグネチャから抽出できることを確認する"""
        chunker = JavaChunker()
        with open(CALCULATOR_PATH) as f:
            source = f.read()
        class_name = chunker.extract_class_name(source)
        assert class_name == "Calculator"


class TestMemberVarExtraction:
    def test_extract_member_vars_from_calculator(self) -> None:
        """Calculator.javaのメンバー変数を正しく抽出できることを確認する"""
        chunker = JavaChunker()
        with open(CALCULATOR_PATH) as f:
            source = f.read()
        member_vars = chunker.extract_member_vars(source)
        assert len(member_vars) >= 2
        assert any("result" in var for var in member_vars)
        assert any("history" in var for var in member_vars)

    def test_extract_member_vars_private(self) -> None:
        """privateメンバー変数を抽出できることを確認する"""
        chunker = JavaChunker()
        source = """
public class Test {
    private int count;
    private String name;
    public void method() {}
}
"""
        member_vars = chunker.extract_member_vars(source)
        assert len(member_vars) == 2
        assert any("count" in var for var in member_vars)
        assert any("name" in var for var in member_vars)

    def test_extract_member_vars_empty(self) -> None:
        """メンバー変数なしで空リストを返すことを確認する"""
        chunker = JavaChunker()
        source = "public class Empty { }"
        member_vars = chunker.extract_member_vars(source)
        assert member_vars == []


class TestMethodChunking:
    def test_chunk_calculator_methods(self) -> None:
        """Calculator.javaを5つのメソッドチャンクに分割できることを確認する"""
        chunker = JavaChunker(token_threshold=10)  # 小さいしきい値でメソッド分割を強制
        chunks = chunker.chunk_file(CALCULATOR_PATH)
        method_names = [
            chunk.metadata.method_name for chunk in chunks if chunk.metadata.method_name
        ]
        assert "add" in method_names
        assert "subtract" in method_names
        assert "multiply" in method_names
        assert "divide" in method_names
        assert "getHistory" in method_names

    def test_chunk_metadata_attached(self) -> None:
        """各チャンクにメタデータが正しく付与されていることを確認する"""
        chunker = JavaChunker(token_threshold=10)  # 小さいしきい値でメソッド分割を強制
        chunks = chunker.chunk_file(CALCULATOR_PATH)
        for chunk in chunks:
            assert chunk.metadata.file_path == CALCULATOR_PATH
            assert chunk.metadata.class_name == "Calculator"
            assert len(chunk.metadata.imports) > 0
            assert chunk.metadata.class_signature != ""

    def test_chunk_type_method(self) -> None:
        """メソッドチャンクのchunk_typeがmethodであることを確認する"""
        chunker = JavaChunker(token_threshold=10)  # 小さいしきい値でメソッド分割を強制
        chunks = chunker.chunk_file(CALCULATOR_PATH)
        # Calculator.javaは10トークンを超えるのでメソッド分割される
        method_chunks = [c for c in chunks if c.metadata.method_name is not None]
        for chunk in method_chunks:
            assert chunk.metadata.chunk_type == "method"


class TestFileChunking:
    def test_small_file_as_single_chunk(self) -> None:
        """1000トークン未満のファイルが1チャンクになることを確認する"""
        chunker = JavaChunker(token_threshold=10000)  # 非常に大きいしきい値
        chunks = chunker.chunk_file(CALCULATOR_PATH)
        # 大きいしきい値の場合はファイル全体が1チャンク
        assert len(chunks) == 1
        assert chunks[0].metadata.chunk_type == "file"

    def test_chunk_type_file(self) -> None:
        """ファイル全体チャンクのchunk_typeがfileであることを確認する"""
        chunker = JavaChunker(token_threshold=10000)
        chunks = chunker.chunk_file(CALCULATOR_PATH)
        assert chunks[0].metadata.chunk_type == "file"


class TestSlidingWindowSplit:
    """_split_if_needed のスライディングウィンドウ分割テスト"""

    def _make_metadata(self) -> object:
        from java_qa_agent.schemas.models import ChunkMetadata

        return ChunkMetadata(
            file_path="/tmp/Test.java",
            class_name="Test",
            chunk_type="method",
        )

    def test_within_limit_returns_single_chunk(self) -> None:
        """max_embed_tokens以内のテキストは1チャンクそのまま返す"""
        chunker = JavaChunker(max_embed_tokens=200, chunk_overlap=20)
        metadata = self._make_metadata()
        content = "public void hello() { System.out.println(\"hi\"); }"
        result = chunker._split_if_needed(content, metadata)  # type: ignore[arg-type]
        assert len(result) == 1
        assert result[0].content == content

    def test_exceeds_limit_returns_multiple_chunks(self) -> None:
        """max_embed_tokensを超えるテキストは複数チャンクに分割される"""
        chunker = JavaChunker(max_embed_tokens=50, chunk_overlap=10)
        metadata = self._make_metadata()
        # 50トークンを確実に超えるテキスト（英単語を大量に並べる）
        content = " ".join(["word"] * 200)
        result = chunker._split_if_needed(content, metadata)  # type: ignore[arg-type]
        assert len(result) > 1

    def test_all_chunks_within_limit(self) -> None:
        """分割後の全チャンクがmax_embed_tokens以内であることを確認する"""
        chunker = JavaChunker(max_embed_tokens=50, chunk_overlap=10)
        metadata = self._make_metadata()
        content = " ".join(["word"] * 200)
        result = chunker._split_if_needed(content, metadata)  # type: ignore[arg-type]
        for chunk in result:
            assert chunk.token_count <= 50

    def test_overlap_between_consecutive_chunks(self) -> None:
        """連続するチャンク間にオーバーラップが存在することを確認する"""
        chunker = JavaChunker(max_embed_tokens=50, chunk_overlap=10)
        metadata = self._make_metadata()
        content = " ".join([f"word{i}" for i in range(200)])
        result = chunker._split_if_needed(content, metadata)  # type: ignore[arg-type]
        assert len(result) >= 2
        # chunk_1の末尾テキストがchunk_2の先頭に含まれる
        end_of_first = result[0].content[-20:]
        assert end_of_first in result[1].content

    def test_last_chunk_contains_end_of_content(self) -> None:
        """最後のチャンクがテキストの末尾を含むことを確認する"""
        chunker = JavaChunker(max_embed_tokens=50, chunk_overlap=10)
        metadata = self._make_metadata()
        last_word = "ENDOFCONTENT"
        content = " ".join(["word"] * 200) + f" {last_word}"
        result = chunker._split_if_needed(content, metadata)  # type: ignore[arg-type]
        assert last_word in result[-1].content

    def test_metadata_preserved_in_all_chunks(self) -> None:
        """分割後の全チャンクにメタデータが引き継がれることを確認する"""
        chunker = JavaChunker(max_embed_tokens=50, chunk_overlap=10)
        metadata = self._make_metadata()
        content = " ".join(["word"] * 200)
        result = chunker._split_if_needed(content, metadata)  # type: ignore[arg-type]
        for chunk in result:
            assert chunk.metadata.class_name == "Test"
            assert chunk.metadata.chunk_type == "method"

    def test_token_count_matches_content(self) -> None:
        """各チャンクのtoken_countがcontentのトークン数と一致することを確認する"""
        import tiktoken

        chunker = JavaChunker(max_embed_tokens=50, chunk_overlap=10)
        metadata = self._make_metadata()
        content = " ".join(["word"] * 200)
        result = chunker._split_if_needed(content, metadata)  # type: ignore[arg-type]
        enc = tiktoken.get_encoding("cl100k_base")
        for chunk in result:
            assert chunk.token_count == len(enc.encode(chunk.content))


class TestEdgeCases:
    def test_large_file_split_by_method(self) -> None:
        """大きいファイルがメソッド単位に分割されることを確認する"""
        # しきい値を1に設定して強制的にメソッド分割
        chunker = JavaChunker(token_threshold=1)
        chunks = chunker.chunk_file(CALCULATOR_PATH)
        assert len(chunks) > 1

    def test_file_with_no_methods(self, tmp_path: Path) -> None:
        """メソッドなしのJavaファイルが全体チャンクになることを確認する"""
        java_file = tmp_path / "Empty.java"
        java_file.write_text("""
package com.example;

/**
 * Empty class
 */
public class Empty {
    // No methods
}
""")
        chunker = JavaChunker(token_threshold=10)
        chunks = chunker.chunk_file(str(java_file))
        assert len(chunks) == 1
        assert chunks[0].metadata.chunk_type == "file"

    def test_chunk_token_count_set(self) -> None:
        """チャンクのtokecn_countが設定されることを確認する"""
        chunker = JavaChunker(token_threshold=10000)
        chunks = chunker.chunk_file(CALCULATOR_PATH)
        assert chunks[0].token_count > 0
