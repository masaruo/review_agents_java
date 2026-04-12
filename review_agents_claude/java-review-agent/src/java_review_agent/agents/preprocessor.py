"""Preprocessor — Javaファイルのトークン推定・メソッド単位チャンキング・コンテキスト付与"""

from __future__ import annotations

import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from java_review_agent.schemas.models import CodeSlot, SkippedItem


def _estimate_tokens(text: str) -> int:
    """簡易トークン数推定: 単語数 × 1.3"""
    return int(len(text.split()) * 1.3)


def _truncate_to_tokens(content: str, max_tokens: int) -> tuple[str, bool]:
    """
    コンテキストを max_tokens 以内に切り詰める。

    Returns:
        (切り詰めたコンテンツ, 切り詰めが発生したか)
    """
    words = content.split()
    estimated = int(len(words) * 1.3)
    if estimated <= max_tokens:
        return content, False

    # max_tokens に収まる単語数を逆算
    target_words = int(max_tokens / 1.3)
    truncated = " ".join(words[:target_words])
    return truncated, True


def _extract_imports(source: str) -> str:
    """import 文全体を抽出する"""
    lines = []
    for line in source.splitlines():
        stripped = line.strip()
        if stripped.startswith("import "):
            lines.append(line)
    return "\n".join(lines)


def _extract_class_signature(source: str) -> str:
    """クラスシグネチャ（クラス名・継承・実装インタフェース）を抽出する"""
    # コメント行を除いた各行から検索する
    pattern = re.compile(
        r"^(?:public|protected|private|abstract|final|static|\s)+"
        r"class\s+\w+(?:\s+extends\s+\w+)?(?:\s+implements\s+[\w,\s]+)?",
        re.MULTILINE,
    )
    match = pattern.search(source)
    if match:
        return match.group(0).strip()
    return ""


def _extract_fields(source: str) -> str:
    """クラスのメンバ変数宣言を抽出する（型名と変数名のみ）"""
    # クラス本体のブロックを取得
    class_body_match = re.search(r"\{(.*)", source, re.DOTALL)
    if not class_body_match:
        return ""

    # フィールド宣言パターン: アクセス修飾子 + 型 + 変数名 + ;
    field_pattern = re.compile(
        r"^\s*(?:(?:public|private|protected|static|final|volatile|transient)\s+)+"
        r"(?!(?:void|class|interface|enum)\b)"
        r"[\w<>\[\],\s]+\s+\w+\s*(?:=.*?)?;",
        re.MULTILINE,
    )
    fields = field_pattern.findall(source)
    return "\n".join(f.strip() for f in fields[:20])  # 最大20フィールド


def _extract_methods(source: str) -> list[tuple[str, str]]:
    """
    メソッド定義を抽出する。

    Returns:
        list of (method_name, method_body) tuples
    """
    # メソッドシグネチャのパターン
    method_pattern = re.compile(
        r"(?:(?:public|private|protected|static|final|abstract|synchronized|native|strictfp)\s+)*"
        r"(?!(?:class|interface|enum|if|for|while|switch|try|catch|new)\b)"
        r"(?:[\w<>\[\],\s]+\s+)?"
        r"(\w+)\s*\([^)]*\)\s*"
        r"(?:throws\s+[\w,\s]+)?\s*\{",
        re.MULTILINE,
    )

    methods: list[tuple[str, str]] = []

    for match in method_pattern.finditer(source):
        method_name = match.group(1)
        # コンストラクタとクラス名の同一チェックはスキップ（シンプル化）
        if method_name in ("class", "interface", "enum", "if", "for", "while", "switch"):
            continue

        start = match.start()
        # ブレースのネストを追跡してメソッド本体を取得
        brace_pos = source.find("{", match.end() - 1)
        if brace_pos == -1:
            continue

        depth = 0
        end = brace_pos
        for i, ch in enumerate(source[brace_pos:], start=brace_pos):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break

        body = source[start:end]
        methods.append((method_name, body))

    return methods


def _build_context_header(imports: str, class_sig: str, fields: str) -> str:
    """各スロットに付与するコンテキストヘッダを生成する"""
    lines = ["// === Context ==="]
    if imports:
        lines.append("// Imports:")
        lines.append(imports)
        lines.append("")
    if class_sig:
        lines.append(f"// Class: {class_sig}")
    if fields:
        lines.append("// Fields:")
        lines.append(fields)
    lines.append("// === Method ===")
    return "\n".join(lines)


def preprocess_file(
    file_path: str,
    chunk_token_threshold: int = 1000,
    max_input_tokens: int = 3000,
) -> tuple[list[CodeSlot], list[SkippedItem]]:
    """
    Javaファイルを読み込み、トークン数を推定して必要に応じてメソッド単位に分割する。

    Args:
        file_path: .java ファイルの絶対パス
        chunk_token_threshold: チャンキング閾値トークン数
        max_input_tokens: 各スロットの最大入力トークン数

    Returns:
        (CodeSlot リスト, SkippedItem リスト)
    """
    path = Path(file_path)
    skipped: list[SkippedItem] = []

    # ファイル読み込み
    try:
        source = path.read_text(encoding="utf-8-sig")
    except Exception as exc:
        skipped.append(
            SkippedItem(
                target=file_path,
                agent_name="preprocessor",
                reason="Parse Error",
                detail=str(exc),
                timestamp=datetime.now(timezone.utc),
            )
        )
        return [], skipped

    # 空ファイルチェック
    if not source.strip():
        skipped.append(
            SkippedItem(
                target=file_path,
                agent_name="preprocessor",
                reason="Parse Error",
                detail="File is empty",
                timestamp=datetime.now(timezone.utc),
            )
        )
        return [], skipped

    token_count = _estimate_tokens(source)

    # 閾値以下 → ファイル全体を1スロット
    if token_count <= chunk_token_threshold:
        content, is_truncated = _truncate_to_tokens(source, max_input_tokens)
        slot = CodeSlot(
            slot_id=f"{file_path}::whole",
            file_path=file_path,
            method_name="whole",
            content=content,
            is_truncated=is_truncated,
        )
        return [slot], skipped

    # 閾値超 → メソッド単位に分割
    imports = _extract_imports(source)
    class_sig = _extract_class_signature(source)
    fields = _extract_fields(source)
    context_header = _build_context_header(imports, class_sig, fields)

    methods = _extract_methods(source)

    # メソッド抽出失敗 → ファイル全体にフォールバック
    if not methods:
        print(
            f"[WARNING] No methods extracted from {file_path}, falling back to whole file.",
            file=sys.stderr,
        )
        content, is_truncated = _truncate_to_tokens(source, max_input_tokens)
        slot = CodeSlot(
            slot_id=f"{file_path}::whole",
            file_path=file_path,
            method_name="whole",
            content=content,
            is_truncated=is_truncated,
        )
        return [slot], skipped

    slots: list[CodeSlot] = []
    for method_name, method_body in methods:
        raw_content = f"{context_header}\n{method_body}"
        content, is_truncated = _truncate_to_tokens(raw_content, max_input_tokens)
        slot = CodeSlot(
            slot_id=f"{file_path}::{method_name}",
            file_path=file_path,
            method_name=method_name,
            content=content,
            is_truncated=is_truncated,
        )
        slots.append(slot)

    return slots, skipped
