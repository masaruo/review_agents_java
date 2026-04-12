import os
from typing import List

def scan_java_files(directory_path: str) -> List[str]:
    """
    指定されたディレクトリから .java ファイルを再帰的にスキャンしてパスのリストを返します。
    
    Args:
        directory_path: スキャン対象のディレクトリパス
        
    Returns:
        List[str]: .java ファイルの絶対パスのリスト
        
    Raises:
        FileNotFoundError: ディレクトリが存在しない場合
    """
    if not os.path.exists(directory_path):
        raise FileNotFoundError(f"Directory not found: {directory_path}")
    
    if not os.path.isdir(directory_path):
        return []

    java_files = []
    for root, _, files in os.walk(directory_path):
        for file in files:
            if file.endswith(".java"):
                java_files.append(os.path.abspath(os.path.join(root, file)))
    
    return sorted(java_files)
