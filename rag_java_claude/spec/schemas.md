# スキーマ定義仕様書

## 概要

全Pydanticモデルの定義。`src/java_qa_agent/schemas/models.py` に実装する。
Pydantic v2 を使用すること。

---

## 設定スキーマ

### OllamaConfig

Ollamaバックエンドの設定。

```python
class OllamaConfig(BaseModel):
    base_url: str = "http://localhost:11434"
    model: str = "qwen2.5-coder:7b"
    embed_model: str = "nomic-embed-text"
    timeout_seconds: int = 120
```

### RagConfig

RAGパイプラインの設定。

```python
class RagConfig(BaseModel):
    top_k: int = 5
    chunk_token_threshold: int = 1000
    max_input_tokens: int = 3000
    max_history_turns: int = 6
```

### StorageConfig

ストレージ設定。

```python
class StorageConfig(BaseModel):
    index_dir: str = "~/.java_qa_agent/indexes"
    log_dir: str = "~/.java_qa_agent/logs"
    save_logs: bool = True
```

### AppConfig

アプリケーション全体の設定。`config.yaml` のルートに対応する。

```python
class AppConfig(BaseModel):
    java_version: int = 17
    ollama: OllamaConfig = Field(default_factory=OllamaConfig)
    rag: RagConfig = Field(default_factory=RagConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
```

---

## チャンクスキーマ

### ChunkMetadata

Javaチャンクのメタデータ。

```python
class ChunkMetadata(BaseModel):
    file_path: str                          # ファイルの絶対パス
    class_name: str                         # クラス名
    method_name: Optional[str] = None       # メソッド名（ファイル全体チャンクはNone）
    imports: list[str] = Field(default_factory=list)      # インポート文リスト
    class_signature: str = ""               # クラスシグネチャ文字列
    member_vars: list[str] = Field(default_factory=list)  # メンバー変数宣言リスト
    chunk_type: str = "method"              # "method" or "file"
```

### JavaChunk

Javaコードチャンク本体。

```python
class JavaChunk(BaseModel):
    content: str        # チャンクのコード内容
    metadata: ChunkMetadata
    token_count: int = 0  # トークン数（エンベディング前に計算）
```

### SearchResult

ChromaDB検索結果。

```python
class SearchResult(BaseModel):
    chunk: JavaChunk
    score: float  # 類似度スコア（0.0〜1.0）
```

---

## 会話スキーマ

### ConversationTurn

会話の1ターン（ユーザーまたはアシスタント）。

```python
class ConversationTurn(BaseModel):
    role: str       # "user" or "assistant"
    content: str    # ターンの内容
    timestamp: datetime = Field(default_factory=datetime.now)
```

### ChatHistory

会話履歴全体。

```python
class ChatHistory(BaseModel):
    turns: list[ConversationTurn] = Field(default_factory=list)
```

#### メソッド
- `add_turn(role: str, content: str) -> None`: ターンを追加する
- `get_recent_turns(n: int) -> list[ConversationTurn]`: 最新n件のターンを返す
- `truncate_to(n_turns: int) -> None`: 先頭から古いターンを削除してn_turns件に切り詰める

---

## プロジェクト管理スキーマ

### ProjectInfo

登録済みプロジェクトの情報。

```python
class ProjectInfo(BaseModel):
    name: str       # プロジェクト名（一意のキー）
    path: str       # Javaプロジェクトのルートディレクトリパス
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
```

### ProjectRegistry

全プロジェクトのレジストリ。`~/.java_qa_agent/projects.json` に保存される。

```python
class ProjectRegistry(BaseModel):
    projects: dict[str, ProjectInfo] = Field(default_factory=dict)
```

- キーはプロジェクト名（`str`）
- 値は `ProjectInfo` インスタンス

---

## バリデーションルール

| モデル | フィールド | バリデーション |
|--------|-----------|--------------|
| OllamaConfig | timeout_seconds | > 0 |
| RagConfig | top_k | >= 1 |
| RagConfig | chunk_token_threshold | >= 1 |
| RagConfig | max_input_tokens | >= 100 |
| RagConfig | max_history_turns | >= 1 |
| ChunkMetadata | chunk_type | "method" または "file" のいずれか |
| SearchResult | score | 0.0 〜 1.0（ChromaDB距離スコアはそのまま使用） |
| ConversationTurn | role | "user" または "assistant" のいずれか |

---

## シリアライゼーション

全モデルは `model.model_dump()` でdictに、`model.model_dump_json()` でJSON文字列に変換できること。
`datetime` フィールドは ISO 8601 形式でシリアライズされること。

---

## 使用例

```python
# AppConfigの生成
config = AppConfig(
    java_version=17,
    ollama=OllamaConfig(model="qwen2.5-coder:7b"),
    rag=RagConfig(top_k=5),
)

# JavaChunkの生成
chunk = JavaChunk(
    content="public int add(int a, int b) { return a + b; }",
    metadata=ChunkMetadata(
        file_path="/path/to/Calculator.java",
        class_name="Calculator",
        method_name="add",
        imports=["import java.util.List;"],
        class_signature="public class Calculator",
        member_vars=["private int result;"],
        chunk_type="method",
    ),
    token_count=15,
)

# ProjectRegistryのCRUD
registry = ProjectRegistry()
project = ProjectInfo(name="my-project", path="/path/to/project")
registry.projects["my-project"] = project
```
