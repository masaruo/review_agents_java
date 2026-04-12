# CLI仕様書

## 概要

`typer` を使用したCLIアプリケーション。エントリポイントは `java-qa` コマンド。

```bash
java-qa [SUBCOMMAND] [OPTIONS]
```

---

## サブコマンド一覧

| サブコマンド | 説明 |
|------------|------|
| `index` | プロジェクトのインデックスを構築（または再構築） |
| `chat` | プロジェクトの対話セッションを開始 |
| `list` | 登録済みプロジェクトの一覧を表示 |
| `delete` | プロジェクトのインデックスを削除 |

---

## `java-qa index`

### 説明
指定ディレクトリのJavaソースコードをスキャン・チャンキング・エンベディングし、ChromaDBに保存する。

### 引数・オプション

| オプション | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `--project` / `-p` | str | ✓ | プロジェクト名（一意の識別子） |
| `--path` / `-d` | str | ✓ | Javaプロジェクトのルートディレクトリパス |

### 正常系の動作
1. プロジェクトをProjectManagerに登録
2. Indexerを起動してインデックスを構築
3. 以下を STDOUT に出力：
   ```
   プロジェクト '<name>' のインデックスを構築中...
   スキャン対象: /path/to/project/src/
   ファイル数: 15件
   チャンク数: 42件
   インデックス構築完了: 42チャンクを保存しました
   ```

### 異常系の動作

| エラー条件 | STDERR出力 | 終了コード |
|-----------|-----------|----------|
| `--path` が存在しない | `エラー: ディレクトリが見つかりません: /path/to/dir` | 1 |
| `.java` ファイルが0件 | `警告: .javaファイルが見つかりませんでした: /path/to/dir/src/` | 0（正常終了） |
| Ollama接続失敗 | Ollama接続エラーメッセージ（components.md参照） | 1 |
| モデル未取得 | モデル未取得エラーメッセージ（components.md参照） | 1 |

### 実行例
```bash
java-qa index --project my-app --path /path/to/my-java-project
java-qa index -p my-app -d /path/to/my-java-project
make index project=my-app path=/path/to/my-java-project
```

---

## `java-qa chat`

### 説明
指定プロジェクトに対して対話セッションを開始する。`exit` または `quit` で終了する。

### 引数・オプション

| オプション | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `--project` / `-p` | str | ✓ | プロジェクト名 |

### 正常系の動作
1. 起動時チェック（Ollama接続・モデル存在・インデックス存在）
2. 以下を STDOUT に表示：
   ```
   Java Q&A Agent - プロジェクト: <name>
   Ollama: qwen2.5-coder:7b
   終了するには 'exit' または 'quit' を入力してください

   質問を入力してください:
   ```
3. ユーザー入力を受け取り、回答をMarkdown形式で表示
4. 次の質問プロンプトを表示（ループ）
5. `exit` または `quit` → セッション終了メッセージ表示後に終了

### 対話セッションの表示フォーマット
```
質問を入力してください: addメソッドについて教えてください

[検索中...]

## 回答

`Calculator` クラスの `add` メソッドは...

（Markdown形式の回答）

質問を入力してください:
```

### 異常系の動作

| エラー条件 | STDERR出力 | 終了コード |
|-----------|-----------|----------|
| 未登録プロジェクト | 登録済みプロジェクト一覧 + エラーメッセージ | 1 |
| インデックス未構築 | `make index` コマンドの実行を促すメッセージ | 1 |
| Ollama接続失敗 | Ollama接続エラーメッセージ | 1 |
| モデル未取得 | モデル未取得エラーメッセージ | 1 |
| LLM出力パースエラー | STDERR にエラー詳細 → セッション継続 | - |

### 実行例
```bash
java-qa chat --project my-app
java-qa chat -p my-app
make chat project=my-app
```

---

## `java-qa list`

### 説明
登録済みプロジェクトの一覧を表示する。

### 引数・オプション
なし

### 正常系の動作
登録済みプロジェクトが存在する場合：
```
登録済みプロジェクト:
  my-app         /path/to/my-java-project         2024-01-01 12:00:00
  another-app    /path/to/another-project          2024-01-02 10:30:00
```

登録済みプロジェクトが0件の場合：
```
登録済みプロジェクトはありません
java-qa index --project <name> --path <dir> でプロジェクトを登録してください
```

### 実行例
```bash
java-qa list
make list
```

---

## `java-qa delete`

### 説明
指定プロジェクトのインデックスをChromaDBから削除し、プロジェクトレジストリから除外する。

### 引数・オプション

| オプション | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `--project` / `-p` | str | ✓ | プロジェクト名 |

### 正常系の動作
1. 確認プロンプトを表示：
   ```
   プロジェクト 'my-app' を削除しますか？ [y/N]:
   ```
2. `y` → インデックス削除 + レジストリ削除
3. 完了メッセージを STDOUT に表示：
   ```
   プロジェクト 'my-app' を削除しました
   ```
4. `N` または Enter → キャンセルメッセージを表示して終了

### 異常系の動作

| エラー条件 | STDERR出力 | 終了コード |
|-----------|-----------|----------|
| 未登録プロジェクト | 登録済みプロジェクト一覧 + エラーメッセージ | 1 |

### 実行例
```bash
java-qa delete --project my-app
java-qa delete -p my-app
make delete project=my-app
```

---

## エラーメッセージフォーマット

### Ollama接続エラー
```
エラー: Ollamaサーバーに接続できません
エンドポイント: http://localhost:11434
エラー種別: ConnectionRefusedError
対処法:
  1. ollama serve コマンドでOllamaを起動してください
  2. または OLLAMA_BASE_URL 環境変数で正しいエンドポイントを設定してください
```

### モデル未取得エラー
```
エラー: モデルが見つかりません: qwen2.5-coder:7b
対処法: 以下のコマンドでモデルを取得してください:
  ollama pull qwen2.5-coder:7b
```

### インデックス未構築エラー
```
エラー: プロジェクト 'my-app' のインデックスが見つかりません
対処法: 以下のコマンドでインデックスを構築してください:
  make index project=my-app path=<Javaプロジェクトのパス>
  または: java-qa index --project my-app --path <Javaプロジェクトのパス>
```

### 未登録プロジェクトエラー
```
エラー: プロジェクト 'unknown-app' は登録されていません
登録済みプロジェクト:
  my-app
  another-app
```

---

## 終了コード

| 終了コード | 意味 |
|-----------|------|
| 0 | 正常終了 |
| 1 | エラー終了 |
