# spec/schemas.md — Pydanticモデル・入出力スキーマ定義

## 配置先：`src/java_review_agent/schemas/models.py`

---

## 0. インタラクティブ指示モデル（★ 新規追加）

```python
from typing import Literal, Optional

ScopeType = Literal["full", "file", "class", "function"]

AgentNameType = Literal[
    "bug_detector",
    "security_scanner",
    "efficiency_analyzer",
    "design_critic",
    "style_reviewer",
]

DEFAULT_AGENTS: list[AgentNameType] = ["bug_detector", "security_scanner"]


class ReviewInstruction(BaseModel):
    scope: ScopeType = "full"
    # scope が "file"/"class"/"function" のとき有効。部分一致フィルタ
    scope_target: Optional[str] = None
    # 実行するエージェント名一覧（デフォルト: bug_detector, security_scanner）
    enabled_agents: list[AgentNameType] = Field(default_factory=lambda: list(DEFAULT_AGENTS))
    # ユーザーのフォーカス質問（Summary Generator のプロンプトに追記される）
    focus_question: Optional[str] = None
```

### フィルタリング仕様

| scope | scope_target の意味 | フィルタ対象 |
|---|---|---|
| `"full"` | 使用しない | 全 `.java` ファイル |
| `"file"` | ファイル名の部分一致文字列 | `Path(p).name` が `scope_target` を含むファイル |
| `"class"` | クラス名の部分一致文字列 | ファイル名が `scope_target` を含むファイル（Javaの慣例でクラス名=ファイル名） |
| `"function"` | メソッド名の完全一致文字列 | Preprocessor が生成した `CodeSlot` の `method_name` が一致するスロットのみ処理 |

---

## 1. 設定モデル

```python
from pydantic import BaseModel, Field
from typing import Optional


class OllamaConfig(BaseModel):
    base_url: str = "http://localhost:11434"
    model: str = "qwen2.5-coder:7b"
    timeout_seconds: int = 120


class ProcessingConfig(BaseModel):
    max_concurrency: int = 1
    chunk_token_threshold: int = 1000
    max_input_tokens: int = 3000
    response_reserve_tokens: int = 1000


class OutputConfig(BaseModel):
    dir: str = "./review_output"


class Config(BaseModel):
    java_version: int = 17
    ollama: OllamaConfig = Field(default_factory=OllamaConfig)
    processing: ProcessingConfig = Field(default_factory=ProcessingConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
```

---

## 2. コードスロットモデル

```python
class CodeSlot(BaseModel):
    slot_id: str           # "{file_path}::{method_name}" or "{file_path}::whole"
    file_path: str         # 元ファイルの絶対パス
    method_name: str       # メソッド名（ファイル全体の場合は "whole"）
    content: str           # レビュー対象コード（コンテキスト付与済み）
    is_truncated: bool = False  # max_input_tokens で切り詰めが発生したか
```

---

## 3. レビュー問題モデル

```python
from typing import Literal

SeverityType = Literal["critical", "major", "minor", "info"]
CategoryType = Literal["bug", "security", "efficiency", "design", "style"]


class ReviewIssue(BaseModel):
    priority: int = Field(ge=1, le=5)   # 1=バグ, 2=セキュリティ, 3=効率性, 4=設計, 5=可読性
    category: CategoryType
    severity: SeverityType
    location: str          # "ClassName#methodName" または行番号情報
    description: str       # 問題の説明
    suggestion: str        # 改善提案
```

---

## 4. エージェント出力モデル

```python
class AgentOutput(BaseModel):
    slot_id: str
    agent_name: str        # "bug_detector" | "security_scanner" | ...
    issues: list[ReviewIssue] = Field(default_factory=list)
    skipped: bool = False
    skip_reason: Optional[str] = None
```

---

## 5. スキップ記録モデル

```python
from datetime import datetime


SkipReasonType = Literal["Resource Limit", "Parse Error", "Connection Error"]


class SkippedItem(BaseModel):
    target: str            # slot_id または file_path
    agent_name: str        # どのエージェントでスキップが発生したか
    reason: SkipReasonType
    detail: str            # 詳細メッセージ（例外メッセージ等）
    timestamp: datetime = Field(default_factory=datetime.utcnow)
```

---

## 6. 集約結果モデル

```python
class AggregatedResult(BaseModel):
    file_path: str
    issues: list[ReviewIssue]          # 優先度昇順・重複除去済み
    skipped_items: list[SkippedItem]   # このファイルに関するスキップ一覧
```

---

## 7. ファイルレポートモデル

```python
class FileReport(BaseModel):
    file_path: str         # 元Javaファイルの絶対パス
    report_path: str       # 保存先Markdownファイルのパス
    content: str           # Markdownコンテンツ
    issue_count: int       # 検出された問題数
```

---

## 8. LangGraph グラフ状態モデル

```python
from typing import TypedDict


class ReviewGraphState(TypedDict):
    # 入力・設定
    project_dir: str
    java_version: int
    config: Config
    review_instruction: ReviewInstruction  # ★ 追加: インタラクティブ指示

    # FileScanner 結果
    java_files: list[str]
    current_file_index: int

    # Preprocessor 結果
    current_file_path: str
    slots: list[CodeSlot]
    current_slot_index: int

    # レビューエージェント結果（スロットごとに累積）
    slot_agent_outputs: list[AgentOutput]  # 現在ファイルの全スロット×全エージェント分

    # Aggregator 結果
    aggregated_result: Optional[AggregatedResult]

    # File Report Generator 結果
    file_reports: list[FileReport]

    # スキップ一覧（全ファイル横断）
    skipped_items: list[SkippedItem]

    # Summary Generator 結果
    summary_content: Optional[str]

    # エラー（致命的エラー時に設定、即時終了）
    fatal_error: Optional[str]
```

---

## 9. Ollama レスポンスパースモデル

LLMからのJSONレスポンスをパースするための一時モデル。

```python
class LLMReviewResponse(BaseModel):
    issues: list[ReviewIssue] = Field(default_factory=list)
```

---

## 10. バリデーション規則

| フィールド | 規則 |
|---|---|
| `ReviewIssue.priority` | 1〜5の整数 |
| `ReviewIssue.severity` | "critical" / "major" / "minor" / "info" のいずれか |
| `ReviewIssue.category` | "bug" / "security" / "efficiency" / "design" / "style" のいずれか |
| `SkippedItem.reason` | "Resource Limit" / "Parse Error" / "Connection Error" のいずれか |
| `CodeSlot.slot_id` | `"{絶対パス}::{メソッド名}"` または `"{絶対パス}::whole"` の形式 |
| `Config.processing.max_concurrency` | 1以上の整数 |
| `Config.processing.chunk_token_threshold` | 100以上の整数 |
| `Config.processing.max_input_tokens` | 500以上の整数 |
