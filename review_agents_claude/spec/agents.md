# spec/agents.md — 各エージェントノード詳細仕様

## 1. FileScanner

### 役割
指定ディレクトリの `src/` 以下を再帰的にスキャンし、`.java` ファイルのパス一覧を取得する。

### 入力
```python
class FileScannerInput(BaseModel):
    project_dir: str   # プロジェクトルートディレクトリの絶対パス
```

### 処理
1. `{project_dir}/src/` ディレクトリが存在するか確認
2. `pathlib.Path.rglob("*.java")` で再帰スキャン
3. 結果をソートして返す

### 出力
```python
class FileScannerOutput(BaseModel):
    java_files: list[str]   # .java ファイルの絶対パス一覧（ソート済み）
```

### エラー処理
- `src/` ディレクトリが存在しない場合：空リスト `[]` を返す（STDERRに警告を出力）
- `.java` ファイルが0件の場合：空リスト `[]` を返す（STDERRに警告を出力）

---

## 2. Preprocessor

### 役割
対象Javaファイルを読み込み、トークン数を推定して、1,000トークン超の場合はメソッド単位に分割する。各スロットにコンテキスト（インポート・クラスシグネチャ・メンバ変数）を付与する。

### 入力
```python
class PreprocessorInput(BaseModel):
    file_path: str                   # .java ファイルの絶対パス
    chunk_token_threshold: int       # チャンキング閾値（デフォルト: 1000）
    max_input_tokens: int            # 最大入力トークン数（デフォルト: 3000）
```

### 処理
1. ファイルを UTF-8 で読み込む（BOMなし・BOMあり両対応）
2. トークン数を推定（`len(content.split()) * 1.3` を目安にした簡易推定）
3. 閾値以下の場合：ファイル全体を1スロットとする
4. 閾値超の場合：以下の手順でメソッド単位に分割
   a. 正規表現でメソッド定義を検出（`public/private/protected/static/abstract` + 型 + メソッド名 + `(` の形式）
   b. 各メソッドのブロック範囲（`{...}`）を抽出
   c. コンテキスト情報を抽出：インポート文全体 / クラスシグネチャ / メンバ変数宣言
   d. 各メソッドスロットにコンテキストを先頭に付与
5. 各スロットのトークン数が `max_input_tokens` を超える場合は先頭から `max_input_tokens` トークン相当に切り詰め

### コンテキスト付与形式（各スロット）
```
// === Context ===
// Imports:
{import文全体}

// Class: {クラスシグネチャ}
// Fields: {メンバ変数宣言（型名のみ、値は省略可）}
// === Method ===
{メソッド本体}
```

### 出力
```python
class CodeSlot(BaseModel):
    slot_id: str           # "{file_path}::{method_name}" or "{file_path}::whole"
    file_path: str         # 元ファイルパス
    method_name: str       # メソッド名（ファイル全体の場合は "whole"）
    content: str           # レビュー対象コード（コンテキスト付与済み）
    is_truncated: bool     # max_input_tokens で切り詰めが発生したか

class PreprocessorOutput(BaseModel):
    slots: list[CodeSlot]
```

### エラー処理
- ファイル読み込み失敗：`SkippedItem(reason="Parse Error", detail=...)` を記録し空リストを返す
- メソッド抽出失敗：ファイル全体を1スロットとしてフォールバック

---

## 3. Bug Detector（優先度1）

### 役割
コードスロット内のバグ・ロジックエラーを検出する（NullPointerException、リソースリーク、ロジックエラー等）。

### 入力
```python
class AgentInput(BaseModel):
    slot: CodeSlot
    java_version: int
```

### 処理
1. プロンプトテンプレートに `{java_version}`, `{code}` を埋め込んでOllamaに送信
2. レスポンスをJSONとしてパース
3. パース失敗時は `Skipped (Parse Error)` として記録

### 出力
```python
class ReviewIssue(BaseModel):
    priority: int           # 1-5（優先度）
    category: str           # "bug" | "security" | "efficiency" | "design" | "style"
    severity: str           # "critical" | "major" | "minor" | "info"
    location: str           # "ClassName#methodName" または行番号情報
    description: str        # 問題の説明
    suggestion: str         # 改善提案

class AgentOutput(BaseModel):
    slot_id: str
    issues: list[ReviewIssue]
    skipped: bool = False
    skip_reason: str | None = None
```

### タイムアウト・リトライ
- タイムアウト：`config.yaml` の `ollama.timeout_seconds`（デフォルト: 120秒）
- リトライ：1回（合計2回試行）
- OOM/タイムアウト後のリトライも失敗した場合：`Skipped (Resource Limit)` として記録

---

## 4. Security Scanner（優先度2）

Bug Detectorと同一インタフェース。プロンプトのみ異なる。

検出対象：SQLインジェクション、コマンドインジェクション、XSS、不適切な認証・認可、機密情報の露出、安全でない乱数生成、安全でない暗号化等。

---

## 5. Efficiency Analyzer（優先度3）

Bug Detectorと同一インタフェース。プロンプトのみ異なる。

検出対象：O(n²)以上のアルゴリズム、適切でないデータ構造の使用、不要なオブジェクト生成、ループ内でのDB/IO呼び出し、文字列連結の非効率（StringBuilderを使うべき箇所等）。

---

## 6. Design Critic（優先度4）

Bug Detectorと同一インタフェース。プロンプトのみ異なる。

検出対象：SOLID原則違反（SRP/OCP/LSP/ISP/DIP）、不適切なデザインパターン適用、過度な結合・低凝集、テスタビリティの低さ。

---

## 7. Style Reviewer（優先度5）

Bug Detectorと同一インタフェース。プロンプトのみ異なる。

**制約**：細かい規約違反の網羅的列挙は行わない。大まかな指摘のみとすること（プロンプトにも明記する）。

---

## 8. Aggregator

### 役割
5つのレビューエージェントの結果を統合し、優先度順に並べ、重複を除去する。

### 入力
```python
class AggregatorInput(BaseModel):
    slot_results: list[AgentOutput]
    file_path: str
```

### 処理
1. 全 `AgentOutput` から `ReviewIssue` を収集
2. 優先度（priority）の昇順でソート
3. 重複除去：同一 `(category, location, description)` の組み合わせで一致するものを除去
4. スキップされたスロット・エージェントを `skipped_items` として記録

### 出力
```python
class AggregatedResult(BaseModel):
    file_path: str
    issues: list[ReviewIssue]     # 優先度順・重複除去済み
    skipped_items: list[SkippedItem]
```

---

## 9. File Report Generator

### 役割
`AggregatedResult` をもとにMarkdownレポートを生成し、ファイルに保存してSTDOUTにも出力する。

### 入力
```python
class FileReportInput(BaseModel):
    aggregated_result: AggregatedResult
    output_dir: str
```

### 処理
1. Markdownテンプレートに結果を埋め込み
2. `{output_dir}/{ファイル名（拡張子なし）}.md` に保存
3. 同内容をSTDOUTに出力

### 出力ファイルフォーマット
```markdown
# Code Review Report: {ファイル名}

**レビュー日時**: {ISO8601形式}
**対象ファイル**: {ファイルパス}

---

## 検出された問題

### [P1] バグ検出

#### 問題1
- **場所**: {location}
- **重要度**: {severity}
- **説明**: {description}
- **改善提案**: {suggestion}

...（優先度順に列挙）

---

## スキップされた項目

| スロット/エージェント | 理由 | 詳細 |
|---|---|---|
| {slot_id} | {reason} | {detail} |
```

### 出力
```python
class FileReport(BaseModel):
    file_path: str
    report_path: str     # 保存先パス
    content: str         # Markdownコンテンツ
```

---

## 10. Summary Generator

### 役割
全ファイルのレビュー結果をもとに、プロジェクト全体のサマリーレポートを生成する。モジュール間の依存関係・データフロー・アーキテクチャ上の推奨事項を評価する。スキップされたファイル/メソッドの一覧を必ず含める。

### 入力
```python
class SummaryInput(BaseModel):
    file_reports: list[FileReport]
    skipped_items: list[SkippedItem]
    java_version: int
```

### 処理
1. 全ファイルの問題一覧をまとめたコンテキストを生成
2. プロンプトテンプレートに埋め込んでOllamaに送信
3. レスポンスをMarkdownとして保存・STDOUT出力

### 出力ファイル：`./review_output/summary.md`

```markdown
# Java Code Review Summary

**プロジェクト**: {project_dir}
**Java Version**: {java_version}
**レビュー日時**: {ISO8601形式}
**処理ファイル数**: {N}件
**スキップ数**: {N}件

---

## アーキテクチャ評価

{LLMによる全体評価}

## 優先度別問題サマリー

| 優先度 | 件数 |
|---|---|
| P1 バグ | N |
| P2 セキュリティ | N |
...

## スキップされたファイル/メソッド一覧

| 対象 | 理由 | 詳細 |
|---|---|---|
| {slot_id or file_path} | {reason} | {detail} |
```

---

## 11. SkippedItem スキーマ

```python
class SkippedItem(BaseModel):
    target: str           # slot_id または file_path
    reason: str           # "Resource Limit" | "Parse Error" | "Connection Error"
    detail: str           # 詳細メッセージ
    timestamp: datetime
```
