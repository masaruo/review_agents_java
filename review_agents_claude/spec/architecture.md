# spec/architecture.md — 全体アーキテクチャ仕様

## 1. システム概要

本システムは、指定したローカルディレクトリ配下の `.java` ファイルを再帰的にスキャンし、LangGraph で定義された複数のAIエージェントノードを用いてコードレビューを行い、Markdownレポートを生成するシステムである。

- **LLMバックエンド**：Ollama (`qwen2.5-coder:7b`)
- **オーケストレーション**：LangGraph
- **出力形式**：Markdownのみ（ファイル保存 + STDOUT）

---

## 2. 入出力仕様

### 入力

| 項目 | 仕様 |
|---|---|
| 形式 | CLIコマンド引数でプロジェクトディレクトリパスを指定 |
| スキャン対象 | 指定ディレクトリの `src/` 以下を再帰的にスキャンし、`.java` ファイルをすべて処理 |
| インタラクティブ指示 | 起動時に対話的なプロンプトで「レビュースコープ」「実行エージェント」「フォーカス質問」を受け付ける |

### インタラクティブ起動フロー

プロジェクトディレクトリが有効であることを確認した後、以下の順で対話的に指示を受け取る：

**Step 1 — レビュースコープの選択**
```
What would you like to review?
  1. Full review (all files)
  2. Specific file(s)  [enter filename pattern, e.g. "UserService.java"]
  3. Specific class    [enter class name, e.g. "UserService"]
  4. Specific function [enter function name, e.g. "authenticate"]
Choice [1-4]:
```

スコープ 2〜4 を選択した場合は、対象名称の入力を促す。

**Step 2 — 実行エージェントの選択**
```
Which agents should run? (press Enter to use defaults: bug, security)
  [1] Bug Detector      (default: ON)
  [2] Security Scanner  (default: ON)
  [3] Efficiency Analyzer (default: OFF)
  [4] Design Critic     (default: OFF)
  [5] Style Reviewer    (default: OFF)
Enter numbers to toggle (e.g. "3 4"), or press Enter to keep defaults:
```

**Step 3 — フォーカス質問（任意）**
```
Any specific question or focus? (optional, press Enter to skip)
> 
```

入力例：`"この認証フローのアーキテクチャはどう思う？"` → Summary Generator のプロンプトに追加される。

### 出力

| 項目 | 仕様 |
|---|---|
| ファイル単位レポート | `./review_output/{filename}.md`（`.java` の拡張子を除いたファイル名） |
| 全体サマリー | `./review_output/summary.md` |
| STDOUT | 各レポートと同一内容を標準出力にも出力 |
| フォーマット | Markdownのみ |

---

## 3. エージェント役割分担

| エージェント | 役割 | 実行方式 |
|---|---|---|
| **FileScanner** | `src/` 以下の `.java` ファイルを再帰スキャン | Python |
| **Preprocessor** | コード読み込み・トークン数推定・メソッド単位チャンキング・メタデータ抽出 | Python |
| **Bug Detector** | バグ・ロジックエラーの検出（優先度1） | Ollama |
| **Security Scanner** | セキュリティ脆弱性の検出（優先度2） | Ollama |
| **Efficiency Analyzer** | アルゴリズム・I/O効率の分析（優先度3） | Ollama |
| **Design Critic** | 設計パターン・SOLID原則の評価（優先度4） | Ollama |
| **Style Reviewer** | 可読性・コーディング規約の大まかな評価（優先度5） | Ollama |
| **Aggregator** | 全エージェント結果の統合・優先度付け・重複除去 | Python（ルールベース） |
| **File Report Generator** | ファイル単位Markdownレポートの生成 | Pythonテンプレート |
| **Summary Generator** | プロジェクト全体サマリー（スキップ一覧含む）の生成 | Ollama |

---

## 4. LangGraph グラフ構造

```
[入力: プロジェクトディレクトリ]
       │
       ▼
[FileScanner] ── src/ 以下の .java ファイルを再帰スキャン
       │
       ▼（ファイルごとにループ）
[Preprocessor] ── トークン数推定 → 1,000トークン超の場合メソッド単位に分割
                   インポート・クラスシグネチャ・メンバ変数を各スロットに付与
       │
       ▼（スロットごと、シリアル実行）
       ├──→ [Bug Detector]
       ├──→ [Security Scanner]
       ├──→ [Efficiency Analyzer]
       ├──→ [Design Critic]
       └──→ [Style Reviewer]
              │（各スロット完了後に集約）
              ▼
       [Aggregator] ── 優先度順に統合・重複除去
              │
              ▼
       [File Report Generator] ── ./review_output/{filename}.md に保存 + STDOUT出力
              │
              ▼（全ファイル処理完了後）
       [Summary Generator] ── プロジェクト全体サマリー + スキップ一覧を生成
              │
              ▼
       [出力: ./review_output/summary.md + STDOUT]
```

**備考**：Concurrency Control要件により、各エージェントへの推論リクエストはシリアルで実行する。LangGraphの並列Send APIは使用しない。

---

## 5. グラフ状態定義（LangGraph State）

```python
class ReviewGraphState(TypedDict):
    project_dir: str                        # 入力プロジェクトディレクトリ
    java_version: int                       # Javaバージョン
    review_instruction: ReviewInstruction   # ★ 追加: ユーザーのインタラクティブ指示
    java_files: list[str]                   # スキャン済み .java ファイルパス一覧
    current_file_index: int                 # 現在処理中のファイルインデックス
    current_file_path: str                  # 現在処理中のファイルパス
    slots: list[CodeSlot]                   # Preprocessor が生成したスロット一覧
    current_slot_index: int                 # 現在処理中のスロットインデックス
    slot_results: list[SlotReviewResult]    # 各スロットのレビュー結果
    aggregated_result: AggregatedResult     # Aggregator の集約結果
    file_reports: list[FileReport]          # 生成済みファイルレポート
    skipped_items: list[SkippedItem]        # スキップされた対象の一覧
    summary: str                            # 全体サマリー（Markdown）
    error: str | None                       # 致命的エラー（即時終了用）
```

---

## 6. ノード遷移条件

| From | To | 条件 |
|---|---|---|
| START | file_scanner | 常に |
| file_scanner | preprocessor | `java_files` が1件以上存在する |
| file_scanner | END | `java_files` が0件（空） |
| preprocessor | bug_detector | 常に（最初のスロット） |
| bug_detector | security_scanner | 常に |
| security_scanner | efficiency_analyzer | 常に |
| efficiency_analyzer | design_critic | 常に |
| design_critic | style_reviewer | 常に |
| style_reviewer | aggregator | 全スロット完了 |
| style_reviewer | bug_detector | 次のスロットが存在する |
| aggregator | file_report_generator | 常に |
| file_report_generator | preprocessor | 次のファイルが存在する |
| file_report_generator | summary_generator | 全ファイル処理完了 |
| summary_generator | END | 常に |

---

## 7. 設定管理（config.yaml）

```yaml
java_version: 17
ollama:
  base_url: "http://localhost:11434"
  model: "qwen2.5-coder:7b"
  timeout_seconds: 120
processing:
  max_concurrency: 1
  chunk_token_threshold: 1000
  max_input_tokens: 3000
  response_reserve_tokens: 1000
output:
  dir: "./review_output"
```

全パラメータは `src/java_review_agent/config.py` の `Config` Pydanticモデルで型安全に管理する。

---

## 8. Concurrency Control

- Ollamaへの推論リクエストはシリアル実行（Max Concurrency: 1）をデフォルトとする
- `config.yaml` の `processing.max_concurrency` パラメータでオーバーライド可能
- `backends/ollama.py` で `asyncio.Semaphore` を使用して制御する

---

## 9. 機能優先度

### P0（必須）

- FileScanner による `.java` ファイルスキャン
- Preprocessor のトークン推定・メソッド単位チャンキング
- 5つのレビューエージェント（Bug/Security/Efficiency/Design/Style）
- Aggregator による結果統合・優先度付け・重複除去
- File Report Generator によるMarkdownレポート生成
- Summary Generator による全体サマリー生成（スキップ一覧含む）
- エラーハンドリング（Ollama未起動・OOM・タイムアウト・パースエラー）
- シリアル実行制御

### P1（重要）

- config.yaml によるパラメータオーバーライド
- `{java_version}` 変数のプロンプトへの埋め込み
- 将来的なフレームワーク固有ルール追加を想定した拡張可能設計

### P2（任意）

- 詳細なデバッグログ出力
- レビュー結果のJSON形式での出力
