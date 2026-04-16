import os
from typing import List

def scan_java_files(directory_path: str, target_files: List[str] = None) -> List[str]:
    """
    指定されたディレクトリから .java ファイルを再帰的にスキャンしてパスのリストを返します。
    
    Args:
        directory_path: スキャン対象のディレクトリパス
        target_files: (Optional) 特定のファイル名またはパスのリスト
        
    Returns:
        List[str]: .java ファイルの絶対パスのリスト
    """
    if not os.path.exists(directory_path):
        raise FileNotFoundError(f"Directory not found: {directory_path}")
    
    if not os.path.isdir(directory_path):
        return []

    java_files = []
    for root, _, files in os.walk(directory_path):
        for file in files:
            if not file.endswith(".java"):
                continue
            
            full_path = os.path.abspath(os.path.join(root, file))
            
            if target_files:
                # ファイル名が target_files に含まれているか、
                # またはフルパスの末尾が target_files のいずれかと一致するか
                matched = False
                for target in target_files:
                    if target in full_path: # シンプルに部分一致で判定（または厳密にファイル名比較）
                        matched = True
                        break
                if not matched:
                    continue
                    
            java_files.append(full_path)
    
    return sorted(java_files)
