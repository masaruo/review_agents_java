"""SCN-xxx: FileScannerテスト"""

from __future__ import annotations

from pathlib import Path

import pytest

from java_review_agent.scanner import scan_java_files


class TestScanJavaFiles:
    def test_scn001_finds_java_files(self, tmp_path: Path) -> None:
        """SCN-001: src/ 配下に複数 .java ファイルが存在する"""
        src = tmp_path / "src"
        src.mkdir()
        (src / "Foo.java").write_text("class Foo {}")
        (src / "Bar.java").write_text("class Bar {}")

        result = scan_java_files(str(tmp_path))

        assert len(result) == 2
        assert all(f.endswith(".java") for f in result)
        # ソート済みであること
        assert result == sorted(result)

    def test_scn002_no_java_files(self, tmp_path: Path) -> None:
        """SCN-002: src/ 配下に .java ファイルが0件 → 空リスト"""
        src = tmp_path / "src"
        src.mkdir()
        (src / "readme.txt").write_text("no java here")

        result = scan_java_files(str(tmp_path))

        assert result == []

    def test_scn003_no_src_dir(self, tmp_path: Path) -> None:
        """SCN-003: src/ ディレクトリが存在しない → 空リスト"""
        result = scan_java_files(str(tmp_path))
        assert result == []

    def test_scn004_recursive_scan(self, tmp_path: Path) -> None:
        """SCN-004: src/ 配下にサブディレクトリがある → 再帰的にスキャン"""
        src = tmp_path / "src"
        subdir = src / "com" / "example"
        subdir.mkdir(parents=True)
        (subdir / "Main.java").write_text("class Main {}")
        (src / "Top.java").write_text("class Top {}")

        result = scan_java_files(str(tmp_path))

        assert len(result) == 2
        file_names = {Path(f).name for f in result}
        assert "Main.java" in file_names
        assert "Top.java" in file_names

    def test_scn005_non_java_files_excluded(self, tmp_path: Path) -> None:
        """SCN-005: .java 以外のファイルが混在しても .java のみ返す"""
        src = tmp_path / "src"
        src.mkdir()
        (src / "Main.java").write_text("class Main {}")
        (src / "build.xml").write_text("<project/>")
        (src / "Main.kt").write_text("class Main")

        result = scan_java_files(str(tmp_path))

        assert len(result) == 1
        assert result[0].endswith("Main.java")
