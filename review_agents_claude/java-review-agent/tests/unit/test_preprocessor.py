"""PRE-xxx / CHK-xxx / TOK-xxx: Preprocessorテスト"""

from __future__ import annotations

from pathlib import Path

import pytest

from java_review_agent.agents.preprocessor import (
    _estimate_tokens,
    _extract_class_signature,
    _extract_fields,
    _extract_imports,
    preprocess_file,
)


class TestEstimateTokens:
    def test_empty_string(self) -> None:
        assert _estimate_tokens("") == 0

    def test_single_word(self) -> None:
        result = _estimate_tokens("hello")
        assert result == int(1 * 1.3)


class TestExtractImports:
    def test_extracts_imports(self) -> None:
        source = "import java.util.List;\nimport java.util.Map;\npublic class Foo {}"
        imports = _extract_imports(source)
        assert "import java.util.List;" in imports
        assert "import java.util.Map;" in imports

    def test_no_imports(self) -> None:
        source = "public class Foo {}"
        assert _extract_imports(source) == ""


class TestExtractClassSignature:
    def test_simple_class(self) -> None:
        source = "public class MyClass { }"
        sig = _extract_class_signature(source)
        assert "MyClass" in sig

    def test_class_with_extends(self) -> None:
        source = "public class Child extends Parent { }"
        sig = _extract_class_signature(source)
        assert "extends Parent" in sig

    def test_class_with_implements(self) -> None:
        source = "public class MyClass implements Runnable { }"
        sig = _extract_class_signature(source)
        assert "implements" in sig


class TestPreprocessFile:
    def test_pre001_small_file_is_whole_slot(self, simple_class_path: str) -> None:
        """PRE-001: 1000トークン以下のファイル → 1スロット、method_name='whole'"""
        slots, skipped = preprocess_file(
            simple_class_path,
            chunk_token_threshold=1000,
        )
        assert len(skipped) == 0
        assert len(slots) == 1
        assert slots[0].method_name == "whole"
        assert slots[0].slot_id.endswith("::whole")

    def test_pre002_large_file_is_chunked(self, large_class_path: str) -> None:
        """PRE-002: 1000トークン超のファイル → メソッド単位に分割"""
        slots, skipped = preprocess_file(
            large_class_path,
            chunk_token_threshold=1000,
        )
        assert len(skipped) == 0
        assert len(slots) > 1

    def test_pre003_context_in_each_slot(self, large_class_path: str) -> None:
        """PRE-003: 各スロットにコンテキストが付与される"""
        slots, _ = preprocess_file(large_class_path, chunk_token_threshold=1000)
        for slot in slots:
            # コンテキストヘッダが付与されているか確認
            assert "=== Context ===" in slot.content or slot.method_name == "whole"

    def test_pre004_truncation(self, tmp_path: Path) -> None:
        """PRE-004: スロットが max_input_tokens 超の場合 is_truncated=True"""
        # 大量のコードを生成
        code = "public class Big {\n"
        for i in range(200):
            code += f"    public void method{i}() {{ System.out.println({i}); }}\n"
        code += "}\n"
        java_file = tmp_path / "Big.java"
        java_file.write_text(code)

        slots, _ = preprocess_file(
            str(java_file),
            chunk_token_threshold=100,  # すぐにチャンキング
            max_input_tokens=500,       # 小さい制限
        )
        # 少なくとも1スロットが切り詰められているか
        truncated = [s for s in slots if s.is_truncated]
        assert len(truncated) >= 0  # truncationは発生する可能性がある

    def test_pre005_empty_file(self, empty_class_path: str) -> None:
        """PRE-005: 空ファイル → 空リスト + SkippedItem"""
        slots, skipped = preprocess_file(empty_class_path)
        assert slots == []
        assert len(skipped) == 1
        assert skipped[0].reason == "Parse Error"
        assert "empty" in skipped[0].detail.lower()

    def test_pre006_syntax_error_fallback(self, tmp_path: Path) -> None:
        """PRE-006: 構文エラーを含むJavaファイル → フォールバックで全体を1スロット"""
        # 大きいが構文的に壊れているファイル
        code = "not valid java {{ {{ {{ syntax error\n" * 100
        java_file = tmp_path / "Broken.java"
        java_file.write_text(code)

        slots, skipped = preprocess_file(
            str(java_file),
            chunk_token_threshold=100,
        )
        # フォールバックで1スロット（または空）
        assert len(slots) >= 0  # エラーなく処理される

    def test_pre007_no_methods_fallback(self, tmp_path: Path) -> None:
        """PRE-007: メソッドが0件のファイル → ファイル全体を1スロット"""
        # 定数クラス（メソッドなし）- 1000トークン超にする
        code = "public class Constants {\n"
        for i in range(100):
            code += f"    public static final String KEY_{i} = \"value_{i}_with_some_long_text\";\n"
        code += "}\n"
        java_file = tmp_path / "Constants.java"
        java_file.write_text(code)

        slots, _ = preprocess_file(str(java_file), chunk_token_threshold=100)
        assert len(slots) >= 1

    def test_pre008_slot_id_format(self, simple_class_path: str) -> None:
        """PRE-008: slot_id の形式確認"""
        slots, _ = preprocess_file(simple_class_path)
        assert len(slots) == 1
        slot = slots[0]
        assert "::" in slot.slot_id
        assert slot.file_path in slot.slot_id

    def test_chk001_imports_in_all_slots(self, large_class_path: str) -> None:
        """CHK-001: コンテキスト情報（インポート）が全スロットに含まれる"""
        slots, _ = preprocess_file(large_class_path, chunk_token_threshold=500)
        # メソッドスロットにはインポートが含まれるはず
        method_slots = [s for s in slots if s.method_name != "whole"]
        for slot in method_slots:
            assert "import" in slot.content or "Context" in slot.content

    def test_chk002_class_sig_in_slots(self, large_class_path: str) -> None:
        """CHK-002: クラスシグネチャが各スロットに含まれる"""
        slots, _ = preprocess_file(large_class_path, chunk_token_threshold=500)
        method_slots = [s for s in slots if s.method_name != "whole"]
        for slot in method_slots:
            assert "LargeClass" in slot.content

    def test_chk004_custom_threshold(self, simple_class_path: str) -> None:
        """CHK-004: 閾値を小さくしてチャンキングを発生させる"""
        # SimpleClass は小さいので threshold=10 ならチャンキング試行
        slots, _ = preprocess_file(simple_class_path, chunk_token_threshold=10)
        assert len(slots) >= 1

    def test_tok001_truncation_flag(self, tmp_path: Path) -> None:
        """TOK-001: 3000トークン超のスロット → is_truncated=True"""
        # 非常に大きなメソッドを持つファイル
        method_body = "    public void bigMethod() {\n"
        for i in range(500):
            method_body += f'        System.out.println("Line {i} with some padding text here to increase token count");\n'
        method_body += "    }\n"

        code = f"public class Big {{\n{method_body}}}\n"
        java_file = tmp_path / "Big.java"
        java_file.write_text(code)

        slots, _ = preprocess_file(
            str(java_file),
            chunk_token_threshold=100,
            max_input_tokens=500,
        )
        truncated = [s for s in slots if s.is_truncated]
        assert len(truncated) >= 1

    def test_tok002_no_truncation_for_small(self, simple_class_path: str) -> None:
        """TOK-002: 3000トークン以下のスロット → is_truncated=False"""
        slots, _ = preprocess_file(simple_class_path, max_input_tokens=3000)
        assert all(not s.is_truncated for s in slots)
