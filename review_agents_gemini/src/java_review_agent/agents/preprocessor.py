import re
from typing import List, Dict, Any

class Preprocessor:
    def __init__(self, chunk_threshold: int = 1000):
        self.chunk_threshold = chunk_threshold

    def _estimate_tokens(self, text: str) -> int:
        # 文字数 / 4 で簡易的にトークン数を推定
        return len(text) // 4

    def _extract_context(self, code: str) -> str:
        """パッケージ、インポート、クラス宣言、メンバ変数を抽出する。"""
        package = re.search(r'package\s+[\w\.]+;', code)
        imports = re.findall(r'import\s+[\w\.\*]+;', code)
        
        # クラス宣言（簡易版）
        class_match = re.search(r'(public|protected|private)?\s*(class|interface|enum)\s+\w+[\s\w,<>]*\{', code)
        
        # メンバ変数（メソッド内以外の単純な宣言を抽出）
        # クラス開始直後から最初のメソッド開始前、またはメソッド外のものを抽出
        # 今回は簡易的に、メソッド宣言（ \w+\(.*\)\s*\{ ）以外のものを探す
        lines = code.split('\n')
        members = []
        in_method = 0
        for line in lines:
            stripped = line.strip()
            if not stripped: continue
            if '{' in line: in_method += line.count('{')
            if '}' in line: in_method -= line.count('}')
            
            # メソッド外で、且つパッケージ/インポート/クラス宣言でないものをメンバとみなす
            if in_method == 1: # クラス内、メソッド外
                if ';' in stripped and not any(k in stripped for k in ['package', 'import', 'class', 'interface', 'enum']):
                    members.append(stripped)

        context = []
        if package: context.append(package.group())
        context.extend(imports)
        if class_match: context.append(class_match.group())
        context.extend(members)
        
        return "\n".join(context)

    def _extract_methods(self, code: str) -> List[str]:
        """メソッドを抽出する。波括弧のバランスを考慮。"""
        # クラス本体（最初の { から最後 } まで）を取得
        body_match = re.search(r'\{([\s\S]*)\}', code)
        if not body_match: return []
        body = body_match.group(1)
        
        methods = []
        current_method = []
        brace_count = 0
        method_started = False
        
        # メソッドのシグネチャらしきものを探す
        # 簡易的に、行の先頭付近に ( があり { で終わる、または { が続くものをメソッド開始とみなす
        lines = body.split('\n')
        for line in lines:
            if not method_started:
                # メソッドシグネチャの判定（簡易版）
                if '(' in line and '{' in line:
                    method_started = True
                    current_method.append(line)
                    brace_count += line.count('{') - line.count('}')
                else:
                    # メンバ変数などはスルー（contextで抽出済み）
                    continue
            else:
                current_method.append(line)
                brace_count += line.count('{') - line.count('}')
                if brace_count == 0:
                    methods.append("\n".join(current_method))
                    current_method = []
                    method_started = False
        
        return methods

    def preprocess(self, code: str) -> List[Dict[str, Any]]:
        token_count = self._estimate_tokens(code)
        
        if token_count <= self.chunk_threshold:
            return [{
                "slot_id": "full_file",
                "content": code,
                "context": "",
                "token_count": token_count
            }]
        
        # チャンキング処理
        context = self._extract_context(code)
        methods = self._extract_methods(code)
        
        if not methods:
            # メソッド抽出に失敗した場合はファイル全体を返す
            return [{
                "slot_id": "full_file",
                "content": code,
                "context": "",
                "token_count": token_count
            }]
            
        slots = []
        for i, method_content in enumerate(methods):
            slots.append({
                "slot_id": f"method_{i}",
                "content": method_content,
                "context": context,
                "token_count": self._estimate_tokens(method_content)
            })
            
        return slots
