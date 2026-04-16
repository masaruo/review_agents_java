import os
import pytest
from src.java_review_agent.scanner import scan_java_files

def test_scan_java_files():
    # フィクスチャディレクトリのパスを取得
    fixture_dir = os.path.join(os.path.dirname(__file__), "..", "fixtures", "sample_java")
    
    # スキャン実行
    java_files = scan_java_files(fixture_dir)
    
    # 相対パスに変換して検証しやすくする
    relative_paths = [os.path.relpath(f, fixture_dir) for f in java_files]
    
    assert "App.java" in relative_paths
    assert "subdir/Service.java" in relative_paths
    assert "not_java.txt" not in relative_paths
    assert len(relative_paths) == 2

def test_scan_java_files_empty_dir(tmp_path):
    # 空のディレクトリでの動作確認
    java_files = scan_java_files(str(tmp_path))
    assert len(java_files) == 0

def test_scan_java_files_non_existent():
    # 存在しないディレクトリでの動作確認
    with pytest.raises(FileNotFoundError):
        scan_java_files("/path/to/non/existent/dir")

def test_scan_java_files_with_targets():
    fixture_dir = os.path.join(os.path.dirname(__file__), "..", "fixtures", "sample_java")
    # ファイル名のみの指定
    target_files = ["App.java"]
    
    java_files = scan_java_files(fixture_dir, target_files=target_files)
    relative_paths = [os.path.relpath(f, fixture_dir) for f in java_files]
    
    assert "App.java" in relative_paths
    assert "subdir/Service.java" not in relative_paths
    assert len(relative_paths) == 1
