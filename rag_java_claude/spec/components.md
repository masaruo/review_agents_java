# コンポーネント詳細仕様書

## 1. FileScanner

### 概要
ディレクトリを再帰的にスキャンして `.java` ファイルを収集するコンポーネント。

### 入力
| パラメータ | 型 | 説明 |
|-----------|-----|------|
| root_dir | str | スキャンするルートディレクトリ（通常は `<project_path>/src/`） |

### 処理
1. `root_dir` が存在しない場合は `FileNotFoundError` を発生させる
2. `root_dir` 以下を再帰的にスキャン
3. 拡張子が `.java` のファイルのみを収集
4. 絶対パスのリストとして返す

### 出力
| 型 | 説明 |
|----|------|
| list[str] | `.java` ファイルの絶対パスリスト |

### エラー処理
- `root_dir` が存在しない → `FileNotFoundError` を発生させる
- 空ディレクトリ → 空リストを返す（エラーにしない）

---

## 2. JavaChunker

### 概要
Javaソースファイルをメソッド単位に分割し、メタデータを付与するコンポーネント。正規表現ベースのパーサーを使用する。

### 入力
| パラメータ | 型 | 説明 |
|-----------|-----|------|
| file_path | str | Javaファイルの絶対パス |
| token_threshold | int | このトークン数未満はファイル全体を1チャンクとして扱う（デフォルト: 1000） |
| max_embed_tokens | int | エンベディングモデルのコンテキスト上限（デフォルト: 768）。これを超えるチャンクはスライディングウィンドウで分割する。tiktoken（BPE）とnomic-embed-text（BERT WordPiece）のトークナイザー差異（約1.5〜2倍）を考慮した保守的な値 |
| chunk_overlap | int | スライディングウィンドウ分割時のオーバーラップトークン数（デフォルト: 200） |

### 処理

#### メタデータ抽出
以下を正規表現で抽出する：

1. **インポート文**
   ```
   パターン: ^import\s+[\w.]+;
   例: import java.util.List;
   ```

2. **クラスシグネチャ**
   ```
   パターン: (public|private|protected)?\s*(abstract|final)?\s*class\s+\w+(\s+extends\s+\w+)?(\s+implements\s+[\w,\s]+)?
   例: public class Calculator extends AbstractCalculator
   ```

3. **メンバー変数**
   ```
   パターン: (private|protected|public)\s+[\w<>\[\]]+\s+\w+\s*[;=]
   例: private int result;
   ```

4. **メソッド**
   ```
   パターン: (public|private|protected|static|\s)+[\w<>\[\]]+\s+(\w+)\s*\([^)]*\)\s*\{
   例: public int add(int a, int b) {
   ```

#### チャンキングロジック
1. ファイル全体のトークン数を計算する（tiktoken cl100k_base）
2. トークン数 < `token_threshold` → ファイル全体を1チャンク（`chunk_type="file"`）
3. トークン数 >= `token_threshold` → メソッド単位に分割（`chunk_type="method"`）
   - メソッドが見つからない場合はファイル全体を1チャンクとしてフォールバック
4. 各チャンクのトークン数が `max_embed_tokens` を超える場合、スライディングウィンドウで複数チャンクに分割する
   - ウィンドウサイズ: `max_embed_tokens` トークン
   - オーバーラップ: `chunk_overlap` トークン（前のチャンクとの重複で文脈を保持）
   - ステップ: `max_embed_tokens - chunk_overlap` トークンずつ進める
   - 例: 5000トークンのメソッド、max=1800、overlap=200 の場合
     - chunk_1: トークン 0〜1800
     - chunk_2: トークン 1600〜3400
     - chunk_3: トークン 3200〜5000
5. 各チャンクにメタデータを付与する（分割チャンクの `chunk_type` は元の種別のまま）

#### メタデータ付与
各チャンク（メソッドまたはファイル全体）に以下のメタデータを付与する：
- `file_path`: ファイルの絶対パス
- `class_name`: クラス名
- `method_name`: メソッド名（ファイル全体チャンクの場合は `None`）
- `imports`: インポート文のリスト
- `class_signature`: クラスシグネチャ文字列
- `member_vars`: メンバー変数宣言のリスト
- `chunk_type`: `"method"` または `"file"`

### 出力
| 型 | 説明 |
|----|------|
| list[JavaChunk] | チャンクのリスト（`JavaChunk` は Pydantic モデル） |

### エラー処理
- ファイルが読み込めない場合（権限エラーなど）→ `IOError` を発生させる
- Javaパースに失敗した場合（正規表現がマッチしない）→ ファイル全体を1チャンクとしてフォールバック

---

## 3. Indexer

### 概要
FileScanner → JavaChunker → OllamaEmbedding → ChromaDB の一連のインデックス構築フローを統括するコンポーネント。

### 入力
| パラメータ | 型 | 説明 |
|-----------|-----|------|
| project_name | str | プロジェクト名（ChromaDBコレクション名に使用） |
| project_path | str | Javaプロジェクトのルートディレクトリ |

### 処理
1. `FileScanner` で `.java` ファイルをスキャン
2. 各ファイルを `JavaChunker` でチャンク化
3. 全チャンクをまとめてバッチエンベディング（`OllamaEmbedding`）
4. ChromaDBの既存コレクションを全削除
5. 新しいチャンクを全件挿入

### ChromaDB設定
- クライアント: `chromadb.PersistentClient`
- 保存先: `~/.java_qa_agent/indexes/{project_name}/`
- コレクション名: `java_chunks`

### 出力
| 型 | 説明 |
|----|------|
| int | インデックスされたチャンク数 |

### エラー処理
- `.java` ファイルが1件もない → 警告メッセージを出力して0を返す
- Ollama接続失敗 → `OllamaConnectionError` を発生させる
- ChromaDB書き込み失敗 → 例外をそのまま伝播させる

---

## 4. Retriever

### 概要
ChromaDBから類似チャンクを検索し、上位 `top_k` 件を返すコンポーネント。

### 入力
| パラメータ | 型 | 説明 |
|-----------|-----|------|
| project_name | str | プロジェクト名 |
| query | str | 検索クエリ（ユーザーの質問文） |
| top_k | int | 取得する最大件数（デフォルト: 5） |

### 処理
1. ChromaDBコレクションを読み込む
2. クエリ文をエンベディング（`OllamaEmbedding`）
3. ChromaDBで類似度検索を実行
4. 結果を `SearchResult` オブジェクトのリストに変換して返す

### 出力
| 型 | 説明 |
|----|------|
| list[SearchResult] | 検索結果リスト（スコア付き） |

### エラー処理
- インデックスが存在しない → `IndexNotFoundError` を発生させる
- 空のインデックス → 空リストを返す
- Ollama接続失敗 → `OllamaConnectionError` を発生させる

---

## 5. ContextBuilder

### 概要
取得チャンク・会話履歴・質問文を結合し、トークン上限内に収まるよう制御するコンポーネント。

### 入力
| パラメータ | 型 | 説明 |
|-----------|-----|------|
| chunks | list[SearchResult] | Retrieverが返した検索結果 |
| history | ChatHistory | 会話履歴 |
| question | str | ユーザーの質問文 |
| max_input_tokens | int | 最大入力トークン数（デフォルト: 3000） |
| java_version | int | Javaバージョン（プロンプトに埋め込む） |

### 処理
1. コードコンテキスト文字列を生成（`spec/prompts.md` のフォーマットに従う）
2. 会話履歴文字列を生成
3. 合計トークン数を計算（tiktoken cl100k_base）
4. 合計 > `max_input_tokens` の場合、古い履歴から1ターンずつ削除して再計算
5. 最終プロンプト文字列を返す

### トークンカウント方法
```python
import tiktoken
encoding = tiktoken.get_encoding("cl100k_base")
token_count = len(encoding.encode(text))
```

### 出力
| 型 | 説明 |
|----|------|
| str | LLMへの入力プロンプト文字列 |

### エラー処理
- チャンクが空 → コードコンテキストなしでプロンプトを生成
- 履歴が空 → 履歴なしでプロンプトを生成
- 質問だけで `max_input_tokens` を超える → 質問をそのまま使用（切り詰めない）

---

## 6. ChatSession

### 概要
マルチターン対話ループを管理するコンポーネント。

### 起動時チェック
以下の順序でチェックを行い、失敗したら即時終了する：

1. **Ollama接続確認**
   - エンドポイント: `config.ollama.base_url`
   - 失敗時: STDERR に以下を出力して `sys.exit(1)`
     ```
     エラー: Ollamaサーバーに接続できません
     エンドポイント: http://localhost:11434
     対処法: ollama serve コマンドでOllamaを起動してください
     ```

2. **推論モデル存在確認**
   - モデル名: `config.ollama.model`
   - 失敗時: STDERR に以下を出力して `sys.exit(1)`
     ```
     エラー: 推論モデルが見つかりません: qwen2.5-coder:7b
     対処法: ollama pull qwen2.5-coder:7b
     ```

3. **エンベディングモデル存在確認**
   - モデル名: `config.ollama.embed_model`
   - 失敗時: STDERR に以下を出力して `sys.exit(1)`
     ```
     エラー: エンベディングモデルが見つかりません: nomic-embed-text
     対処法: ollama pull nomic-embed-text
     ```

4. **インデックス存在確認**
   - プロジェクトのChromaDBコレクションが存在するか
   - 失敗時: STDERR に以下を出力して `sys.exit(1)`
     ```
     エラー: プロジェクト '<name>' のインデックスが見つかりません
     対処法: make index project=<name> path=<path>
     ```

### 対話ループ
1. ユーザーから入力を受け取る
2. `"exit"` または `"quit"` → ループを終了
3. `Retriever` で関連チャンクを取得
4. `ContextBuilder` でプロンプトを構築
5. `OllamaLLM` で回答を生成（LLMパースエラーは `try/except` で捕捉し、STDERR出力後に継続）
6. STDOUT に Markdown 形式で出力
7. `SessionLogger` でログを保存
8. `ChatHistory` に追加（最大 `max_history_turns` ターン）

### 履歴管理
- `ChatHistory.turns` リストの長さが `max_history_turns * 2`（user + assistant のペア）を超えたら、先頭から削除する

---

## 7. ProjectManager

### 概要
プロジェクトの登録・取得・削除・一覧表示を管理するコンポーネント。

### データストア
- ファイル: `~/.java_qa_agent/projects.json`
- フォーマット: `ProjectRegistry` モデルのJSON

### メソッド一覧

#### `register(name: str, path: str) -> ProjectInfo`
- `ProjectInfo` を作成して `ProjectRegistry` に追加
- `~/.java_qa_agent/projects.json` を更新
- 既存プロジェクト名の場合は `updated_at` を更新して上書き

#### `get(name: str) -> ProjectInfo`
- プロジェクトが存在しない場合 → `ProjectNotFoundError` を発生させる
  - エラーメッセージに登録済みプロジェクト一覧を含める

#### `delete(name: str) -> None`
- プロジェクトが存在しない場合 → `ProjectNotFoundError`
- `projects.json` からプロジェクトを削除
- `~/.java_qa_agent/indexes/{name}/` ディレクトリを削除

#### `list_projects() -> list[ProjectInfo]`
- 登録済みプロジェクトの一覧を返す
- 空の場合は空リストを返す

### エラー処理
- `projects.json` が存在しない → 空の `ProjectRegistry` として扱う（新規作成）
- `projects.json` の読み込み失敗 → `IOError` を発生させる

---

## 8. SessionLogger

### 概要
セッションの会話ログを JSONL 形式で保存するコンポーネント。

### ログ保存先
`~/.java_qa_agent/logs/{project_name}/{timestamp}.jsonl`

- `timestamp` フォーマット: `YYYYMMDD_HHMMSS`

### ログフォーマット
各行は `ConversationTurn` の JSON 表現：
```json
{"role": "user", "content": "addメソッドの実装を説明してください", "timestamp": "2024-01-01T12:00:00"}
{"role": "assistant", "content": "addメソッドは...", "timestamp": "2024-01-01T12:00:01"}
```

### メソッド一覧

#### `log_turn(turn: ConversationTurn) -> None`
- `config.storage.save_logs` が `False` の場合は何もしない
- ログディレクトリが存在しない場合は自動作成
- 1行のJSONとしてファイルに追記

---

## 9. OllamaLLM（backends/ollama_llm.py）

### 抽象インタフェース
```python
class LLMBackend(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> str: ...
    
    @abstractmethod
    def check_connection(self) -> bool: ...
    
    @abstractmethod
    def check_model_available(self, model_name: str) -> bool: ...
```

### OllamaLLM実装
- `ollama.Client` を使用
- `generate()`: `ollama.Client.generate()` を呼び出す
- `check_connection()`: `/api/tags` エンドポイントへの接続確認
- `check_model_available()`: モデルリストに指定モデルが含まれるか確認
- タイムアウト: `config.ollama.timeout_seconds`
- シリアル実行（並列化なし）

---

## 10. OllamaEmbedding（backends/ollama_embed.py）

### 抽象インタフェース
```python
class EmbeddingBackend(ABC):
    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]: ...
    
    @abstractmethod
    def embed_query(self, text: str) -> list[float]: ...
```

### OllamaEmbedding実装
- `ollama.Client` を使用
- `embed()`: テキストリストをバッチでエンベディング（1テキストずつ呼び出しを繰り返す）
- `embed_query()`: 1件のテキストをエンベディング
- モデル: `config.ollama.embed_model`

---

## 11. AppConfig（config.py）

### 概要
`config.yaml` を読み込み、環境変数でマージし、シングルトンとして提供するコンポーネント。

### 設定読み込み優先順位
1. 環境変数（`.env` ファイル経由）
2. `config.yaml`
3. デフォルト値（Pydanticモデルのデフォルト）

### 環境変数マッピング
| 環境変数 | config.yamlパス |
|---------|----------------|
| `OLLAMA_BASE_URL` | `ollama.base_url` |

### 提供インタフェース
```python
def get_config() -> AppConfig:
    """シングルトンのAppConfigインスタンスを返す"""
    ...

def load_config(config_path: str | None = None) -> AppConfig:
    """指定パスのconfig.yamlを読み込む（テスト用）"""
    ...
```
