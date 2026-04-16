# spec/test-plan.md — テスト計画・テストケース一覧

## テストフレームワーク

- `pytest` + `pytest-asyncio`
- モック：`unittest.mock` / `pytest-mock`
- フィクスチャ：`tests/fixtures/sample_java/` に配置したJavaファイル

---

## テストディレクトリ構成

```
tests/
├── conftest.py                    # 共通フィクスチャ（config, sample_slots等）
├── unit/
│   ├── test_config.py             # 設定管理テスト
│   ├── test_scanner.py            # FileScannerテスト
│   ├── test_preprocessor.py      # Preprocessorテスト（チャンキング・コンテキスト付与）
│   ├── test_aggregator.py         # Aggregatorテスト
│   ├── test_file_report_generator.py
│   ├── test_agents.py             # 各レビューエージェントテスト（Ollamaモック）
│   └── test_schemas.py            # Pydanticモデルバリデーションテスト
├── integration/
│   ├── test_ollama_connection.py  # Ollama通信テスト（モック可）
│   └── test_graph.py              # LangGraph遷移テスト
└── fixtures/
    └── sample_java/
        ├── SimpleClass.java        # 正常・小規模ファイル
        ├── LargeClass.java         # 1000トークン超のファイル（チャンキングテスト用）
        ├── BuggyClass.java         # 既知のバグパターンを含むファイル
        ├── SecurityVulnerable.java # セキュリティ脆弱性を含むファイル
        ├── EmptyClass.java         # 空ファイル（0バイト）
        ├── SyntaxError.java        # 構文エラーを含むファイル
        └── InefficiencyClass.java  # 効率性問題を含むファイル
```

---

## 1. 単体テスト（unit/）

### 1.1 test_config.py — 設定管理テスト

| テストID | テスト内容 | 期待結果 |
|---|---|---|
| CFG-001 | デフォルト値で Config を生成 | `java_version=17`, `max_concurrency=1` 等のデフォルト値 |
| CFG-002 | config.yaml から設定を読み込み | ファイルの値が正しくロードされる |
| CFG-003 | 不正な `max_concurrency: 0` | `ValidationError` が発生する |
| CFG-004 | 不正な `chunk_token_threshold: 50` | `ValidationError` が発生する |
| CFG-005 | 存在しない config.yaml | デフォルト値で動作する |

### 1.2 test_scanner.py — FileScannerテスト

| テストID | テスト内容 | 期待結果 |
|---|---|---|
| SCN-001 | `src/` 配下に複数 `.java` ファイルが存在する | パス一覧が返される（ソート済み） |
| SCN-002 | `src/` 配下に `.java` ファイルが0件 | 空リスト `[]`、STDERRに警告 |
| SCN-003 | `src/` ディレクトリが存在しない | 空リスト `[]`、STDERRに警告 |
| SCN-004 | `src/` 配下にサブディレクトリがある | 再帰的にスキャンされる |
| SCN-005 | `.java` 以外のファイル（`.kt`, `.xml` 等）が混在 | `.java` ファイルのみが返される |
| SCN-006 | `scope="file"`, `scope_target="UserService"` | `UserService.java` を含むファイルのみ返される |
| SCN-007 | `scope="class"`, `scope_target="UserService"` | `stem` が `UserService` を含むファイルのみ返される |
| SCN-008 | `scope="function"` | ファイルフィルタなし（全ファイルが返される） |
| SCN-009 | `scope="file"`, `scope_target` に一致するファイルなし | 空リスト `[]`、STDERRに警告 |
| SCN-010 | `instruction=None` | フィルタなし・全ファイルが返される（後方互換） |

### 1.3 test_preprocessor.py — Preprocessorテスト（チャンキング）

| テストID | テスト内容 | 期待結果 |
|---|---|---|
| PRE-001 | 1000トークン以下のファイル | スロット1件、`method_name="whole"` |
| PRE-002 | 1000トークン超のファイル（複数メソッド） | メソッド単位に分割された複数スロット |
| PRE-003 | 各スロットにコンテキストが付与される | インポート・クラスシグネチャ・メンバ変数が先頭に含まれる |
| PRE-004 | スロットが3000トークン超 | `is_truncated=True`、内容が切り詰められる |
| PRE-005 | 空ファイル（0バイト） | 空のスロットリスト、SkippedItemに記録 |
| PRE-006 | 構文エラーを含むJavaファイル | メソッド抽出失敗→ファイル全体を1スロットにフォールバック |
| PRE-007 | メソッドが0件のファイル（定数クラス等） | ファイル全体を1スロット |
| PRE-008 | `slot_id` の形式確認 | `"{ファイルパス}::{メソッド名}"` または `"{ファイルパス}::whole"` |

### 1.4 test_aggregator.py — Aggregatorテスト

| テストID | テスト内容 | 期待結果 |
|---|---|---|
| AGG-001 | 優先度順（1→5）にソートされる | priority昇順で並んでいる |
| AGG-002 | 同一 `(category, location, description)` の重複除去 | 重複が1件に集約される |
| AGG-003 | 全エージェントが正常終了 | `skipped_items` が空 |
| AGG-004 | 一部エージェントがスキップ | スキップ情報が `skipped_items` に記録される |
| AGG-005 | 問題が0件 | 空の `issues` リスト |

### 1.5 test_agents.py — レビューエージェントテスト（Ollamaモック）

| テストID | テスト内容 | 期待結果 |
|---|---|---|
| AGT-001 | Bug Detector: 正常なJSONレスポンス | `ReviewIssue` リストが返される |
| AGT-002 | Security Scanner: 正常なJSONレスポンス | `ReviewIssue` リストが返される |
| AGT-003 | Efficiency Analyzer: 正常なJSONレスポンス | `ReviewIssue` リストが返される |
| AGT-004 | Design Critic: 正常なJSONレスポンス | `ReviewIssue` リストが返される |
| AGT-005 | Style Reviewer: 正常なJSONレスポンス | `ReviewIssue` リストが返される |
| AGT-006 | LLMが不正なJSON返却 | `skipped=True`, `skip_reason="Parse Error"` |
| AGT-007 | OOM エラー発生 | `skipped=True`, `skip_reason="Resource Limit"` |
| AGT-008 | タイムアウト発生 | `skipped=True`, `skip_reason="Resource Limit"` |
| AGT-009 | `{java_version}` がプロンプトに埋め込まれる | プロンプト文字列に正しいバージョンが含まれる |
| AGT-010 | リトライ：1回失敗→2回目成功 | 正常な結果が返される |
| AGT-011 | リトライ：2回とも失敗 | `skipped=True`, `skip_reason="Resource Limit"` |

### 1.6 test_schemas.py — Pydanticモデルバリデーションテスト

| テストID | テスト内容 | 期待結果 |
|---|---|---|
| SCH-001 | `ReviewIssue` の正常生成 | 全フィールドが正しく設定される |
| SCH-002 | `priority=0`（範囲外） | `ValidationError` |
| SCH-003 | `priority=6`（範囲外） | `ValidationError` |
| SCH-004 | `severity="unknown"`（不正な値） | `ValidationError` |
| SCH-005 | `category="unknown"`（不正な値） | `ValidationError` |
| SCH-006 | `SkippedItem` の `reason` が不正 | `ValidationError` |
| SCH-007 | `CodeSlot` の正常生成 | 全フィールドが正しく設定される |
| SCH-008 | `Config` デフォルト値の確認 | 全フィールドがデフォルト値 |
| SCH-009 | `ReviewInstruction` デフォルト値 | `scope="full"`, `enabled_agents=["bug_detector","security_scanner"]`, `focus_question=None` |
| SCH-010 | `ReviewInstruction.scope` に不正な値 | `ValidationError` |
| SCH-011 | `ReviewInstruction.enabled_agents` に不正なエージェント名 | `ValidationError` |
| SCH-012 | `ReviewInstruction.enabled_agents` が空リスト | 正常に生成される（バリデーションエラーなし） |

---

## 2. スキーマテスト（schemas/）

上記 `test_schemas.py` に含まれる（1.6 参照）。

---

## 3. グラフ遷移テスト（integration/test_graph.py）

| テストID | テスト内容 | 期待結果 |
|---|---|---|
| GRP-001 | `.java` ファイルあり → 正常フロー | FileScanner → Preprocessor → レビューエージェント群 → Aggregator → FileReport → Summary の順に遷移 |
| GRP-002 | `.java` ファイルなし | FileScanner → END（サマリー生成なし） |
| GRP-003 | 複数ファイル処理 | 全ファイル処理後にSummaryGeneratorが呼ばれる |
| GRP-004 | シリアル実行の確認 | 各エージェントへの推論が逐次実行される（並列送信されない） |
| GRP-005 | Ollama未起動時 | 起動時チェックで `fatal_error` が設定され即時終了 |

---

## 4. 統合テスト — Ollama通信テスト（integration/test_ollama_connection.py）

| テストID | テスト内容 | 期待結果 |
|---|---|---|
| OLL-001 | 接続確認（モック）：成功 | 正常終了 |
| OLL-002 | 接続確認（モック）：失敗 | STDERRにエラー種別・エンドポイント・推奨対処が出力され `SystemExit` |
| OLL-003 | 推論リクエスト（モック）：正常 | レスポンスが返される |
| OLL-004 | 推論リクエスト（モック）：タイムアウト | `TimeoutError` が発生する |
| OLL-005 | セマフォによるシリアル実行 | 同時リクエストが `max_concurrency` を超えない |

---

## 5. チャンキングテスト

上記 `test_preprocessor.py` の PRE-001〜PRE-008 に含まれる。

追加ケース：

| テストID | テスト内容 | 期待結果 |
|---|---|---|
| CHK-001 | コンテキスト情報（インポート）が全スロットに含まれる | 各スロットの `content` にインポート文が存在する |
| CHK-002 | コンテキスト情報（クラスシグネチャ）が全スロットに含まれる | 各スロットの `content` にクラス定義が存在する |
| CHK-003 | コンテキスト情報（メンバ変数）が全スロットに含まれる | 各スロットの `content` にフィールド宣言が存在する |
| CHK-004 | 閾値をconfig.yamlでオーバーライド（500トークン） | 500トークン超でチャンキングが発生する |

---

## 6. トークン制限テスト

| テストID | テスト内容 | 期待結果 |
|---|---|---|
| TOK-001 | 3000トークン超のスロット | `is_truncated=True`、`len(content.split()) * 1.3 <= 3000` |
| TOK-002 | 3000トークン以下のスロット | `is_truncated=False`、内容がそのまま |
| TOK-003 | `max_input_tokens` をconfig.yamlで変更（2000） | 2000トークンで切り詰めが発生する |

---

## 7. エラーハンドリングテスト

| テストID | テスト内容 | 期待結果 |
|---|---|---|
| ERR-001 | Ollama未起動時の起動チェック | STDERR: エラー種別・エンドポイント・推奨対処。`SystemExit` |
| ERR-002 | OOMエラー発生後のスキャン継続 | 該当スロットが `Skipped (Resource Limit)` として記録され、次のスロット/ファイルが処理される |
| ERR-003 | タイムアウト後のスキャン継続 | 同上 |
| ERR-004 | LLMパースエラー | `Skipped (Parse Error)` として記録される |
| ERR-005 | スキップ一覧がサマリーに含まれる | `summary.md` にスキップ一覧テーブルが存在する |
| ERR-006 | ファイル読み込み失敗 | `Skipped (Parse Error)` として記録され処理継続 |

---

## 8. 回帰テスト

### 8.1 既知のバグパターン（`BuggyClass.java` を使用）

| テストID | 内容 |
|---|---|
| REG-001 | NullPointerException リスク（null チェックなし） |
| REG-002 | リソースリーク（try-with-resources 未使用） |
| REG-003 | 配列インデックス境界違反 |

### 8.2 既知のセキュリティ脆弱性（`SecurityVulnerable.java` を使用）

| テストID | 内容 |
|---|---|
| REG-004 | SQL インジェクション（文字列連結によるクエリ構築） |
| REG-005 | ハードコードされたパスワード |

---

## 9. エッジケーステスト

| テストID | テスト内容 | 期待結果 |
|---|---|---|
| EDG-001 | 空ファイル（0バイト） | `Skipped (Parse Error)` として記録 |
| EDG-002 | 巨大ファイル（5000トークン超・複数メソッド） | 正常にチャンキングされ全スロットが処理される |
| EDG-003 | 構文エラーを含むJavaファイル | フォールバックでファイル全体を1スロットとして処理 |
| EDG-004 | `src/` 配下に `.java` ファイルが存在しない | STDERR警告を出力してENDへ遷移 |
| EDG-005 | `review_output/` ディレクトリが存在しない | 自動作成されレポートが保存される |
| EDG-006 | 同名ファイルが異なるサブディレクトリに存在 | それぞれ別レポートとして出力される（パスを含む名前で区別） |

---

## テストフィクスチャ仕様

### `SimpleClass.java`（100トークン以下）
```java
public class SimpleClass {
    public int add(int a, int b) {
        return a + b;
    }
}
```

### `LargeClass.java`（2000トークン以上）
- 10以上のメソッドを持つクラス
- チャンキングのトリガーとなる十分な量のコード

### `BuggyClass.java`
- NullPointerExceptionリスクのあるコード
- unclosed stream のコード
- 配列境界チェックなしのコード

### `SecurityVulnerable.java`
- SQLインジェクション脆弱なコード（文字列連結でSQL構築）
- ハードコードされたパスワード
