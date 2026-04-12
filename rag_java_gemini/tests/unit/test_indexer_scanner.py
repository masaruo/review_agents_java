
import pytest

from java_qa_agent.indexer import FileScanner


@pytest.fixture
def sample_java_project(tmp_path):
    src_dir = tmp_path / "src"
    src_dir.mkdir()

    # Valid Java files
    (src_dir / "Main.java").write_text("public class Main {}")

    pkg_dir = src_dir / "com" / "example"
    pkg_dir.mkdir(parents=True)
    (pkg_dir / "Service.java").write_text(
        "package com.example; public class Service {}"
    )

    # Invalid files (should be ignored)
    (src_dir / "readme.txt").write_text("hello")
    (tmp_path / "Other.java").write_text("not in src")

    return tmp_path


def test_file_scanner_scan(sample_java_project):
    scanner = FileScanner(root_dir=sample_java_project)
    files = scanner.scan()

    assert len(files) == 2
    filenames = [f.name for f in files]
    assert "Main.java" in filenames
    assert "Service.java" in filenames
    for f in files:
        assert str(f).startswith(str(sample_java_project / "src"))
