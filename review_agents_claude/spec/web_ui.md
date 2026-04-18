# spec/web_ui.md — Web UI + 追加質問機能 仕様

## 1. 概要

レビュー完了後、ブラウザ上でレビュー結果に対して追加質問できるWeb UIを追加する。
既存のCLI・LangGraphパイプラインはそのまま維持し、新たにFastAPIサーバーを追加する。

---

## 2. ユースケース

1. ブラウザでプロジェクトディレクトリとレビュー設定を入力し、レビューを開始する
2. レビュー結果（summary.md の内容）がブラウザに表示される
3. ユーザーが「このバグの修正方法は？」などの追加質問を入力する
4. Ollamaがレビュー結果をコンテキストとして追加質問に回答する
5. 会話を繰り返せる（チャット履歴を保持）

---

## 3. アーキテクチャ

```
[ブラウザ]
  ├── GET  /browse?path=<dir> → ディレクトリ一覧取得（ディレクトリピッカー用）
  ├── POST /review      → レビュー実行（既存グラフを呼び出し）
  ├── GET  /review/{id} → レビュー結果取得
  └── POST /chat/{id}   → 追加質問（会話継続、SSEストリーミング）
         ↕
[FastAPI サーバー (src/java_review_agent/server.py)]
  ├── レビュー実行: 既存の build_graph() を呼び出す
  ├── セッション管理: レビュー結果 + チャット履歴をメモリ上で保持
  └── 追加質問: レビュー結果 + 履歴をコンテキストにOllamaへ問い合わせ
         ↕
[Ollama]
```

---

## 4. 新規ファイル構成

```
java-review-agent/
├── src/java_review_agent/
│   ├── server.py          ← FastAPIアプリ（新規）
│   └── chat.py            ← 追加質問ハンドラ（新規）
└── static/
    └── index.html         ← シングルページUI（新規）
```

---

## 5. APIエンドポイント仕様

### GET /browse
サーバー側のディレクトリ一覧を返す（ディレクトリピッカーUI用）。

**クエリパラメータ**
- `path`（省略時はホームディレクトリ）

**レスポンス**
```json
{
  "current": "/Users/foo/projects",
  "parent": "/Users/foo",
  "entries": [
    {"name": "my-app", "path": "/Users/foo/projects/my-app", "is_dir": true},
    {"name": "other",  "path": "/Users/foo/projects/other",  "is_dir": true}
  ]
}
```
ディレクトリのみ返す（ファイルは除外）。

---

### POST /review
レビューを開始する。バックグラウンドタスクとして実行。

**リクエスト**
```json
{
  "project_dir": "/path/to/project",
  "scope": "full",
  "enabled_agents": ["bug_detector", "security_scanner"],
  "focus_question": null
}
```

**レスポンス**
```json
{
  "session_id": "uuid",
  "status": "running"
}
```

### GET /review/{session_id}
レビュー結果を取得する。

**レスポンス**
```json
{
  "session_id": "uuid",
  "status": "running" | "done" | "error",
  "summary": "## レビューサマリー...",
  "file_reports": [{"filename": "Foo.java", "content": "..."}],
  "error": null
}
```

### POST /chat/{session_id}
レビュー結果に対して追加質問する（SSEストリーミング）。

**リクエスト**
```json
{
  "message": "NullPointerExceptionのバグはどう修正すればいい？"
}
```

**レスポンス（SSEストリーミング）**
```
data: {"delta": "NullPointerException"}
data: {"delta": "を修正するには..."}
data: [DONE]
```

---

## 6. セッション管理

- セッションはサーバーのメモリ上に保持（`dict[str, ReviewSession]`）
- セッションデータ：`session_id`, `status`, `summary`, `file_reports`, `chat_history`, `error`
- セッションTTLは設定なし（プロセス再起動で消える設計）

---

## 7. 追加質問のコンテキスト構成

Ollamaへ送るプロンプト（チャット形式）：

```
[システムメッセージ]
あなたはJavaコードレビューの専門家です。
以下のコードレビュー結果を参照して、ユーザーの質問に日本語で回答してください。

[レビュー結果コンテキスト]
{summary の内容 + 各ファイルレポートの内容}

[会話履歴 + 現在の質問]（messagesリスト形式）
```

---

## 8. フロントエンド（index.html）

- 単一HTMLファイル（追加ライブラリ不要、Vanilla JS）
- 画面構成：
  - 左ペイン：レビュー設定フォーム（project_dir, scope, agents, focus_question）
  - 右ペイン上段：レビュー結果表示（Markdown→プレーンテキスト）
  - 右ペイン下段：チャット入力欄 + 会話履歴

### ディレクトリピッカー

- project_dir 入力欄の右に「参照」ボタンを配置
- クリックするとモーダルが開き、`GET /browse` でサーバー側のディレクトリを表示
- 現在のパスをパンくずリスト形式で表示
- ディレクトリ名をクリックすると下位ディレクトリへ移動
- 「このディレクトリを選択」ボタンで確定 → project_dir 入力欄に反映してモーダルを閉じる

---

## 9. 依存関係追加

```toml
[project]
dependencies = [
  "fastapi>=0.110.0",
  "uvicorn>=0.29.0",
  "sse-starlette>=2.0.0",
]
```

---

## 10. 既存コードへの変更

| ファイル | 変更内容 |
|---|---|
| `main.py` | 変更なし（CLI機能は維持） |
| `graph.py` | 変更なし |
| `pyproject.toml` | fastapi/uvicorn/sse-starlette を追加 |
