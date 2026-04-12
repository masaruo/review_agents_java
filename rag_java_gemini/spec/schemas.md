# SPEC: データスキーマ (schemas.md)

## 1. 構成
システムの核となる Pydantic モデルと設定ファイルの構造を定義する。

## 2. Pydantic モデル

### 2.1. `Config` (config.yaml)
- `java_version`: int (デフォルト: 17)
- `ollama`:
  - `base_url`: str (例: "http://localhost:11434")
  - `model`: str (例: "qwen2.5-coder:7b")
  - `embed_model`: str (例: "nomic-embed-text")
  - `timeout_seconds`: int (デフォルト: 120)
- `rag`:
  - `top_k`: int (デフォルト: 5)
  - `chunk_token_threshold`: int (デフォルト: 1000)
  - `max_input_tokens`: int (デフォルト: 3000)
  - `max_history_turns`: int (デフォルト: 6)
- `storage`:
  - `index_dir`: str (デフォルト: "~/.java_qa_agent/indexes")
  - `log_dir`: str (デフォルト: "~/.java_qa_agent/logs")
  - `save_logs`: bool (デフォルト: true)

### 2.2. `JavaChunk`
- `content`: str (チャンク内容)
- `metadata`:
  - `file_path`: str
  - `imports`: str
  - `class_signature`: str
  - `member_variables`: str
  - `chunk_type`: str (method/full_file)

### 2.3. `Project`
- `name`: str
- `path`: str
- `indexed_at`: datetime (オプション)

### 2.4. `ChatMessage`
- `role`: str (user/assistant)
- `content`: str
- `timestamp`: datetime

## 3. 設定ファイル構成 (config.yaml)
```yaml
java_version: 17
ollama:
  base_url: "http://localhost:11434"
  model: "qwen2.5-coder:7b"
  embed_model: "nomic-embed-text"
  timeout_seconds: 120
rag:
  top_k: 5
  chunk_token_threshold: 1000
  max_input_tokens: 3000
  max_history_turns: 6
storage:
  index_dir: "~/.java_qa_agent/indexes"
  log_dir: "~/.java_qa_agent/logs"
  save_logs: true
```

## 4. プロジェクト管理データ構造 (projects.json)
```json
{
  "projects": {
    "my_project": {
      "path": "/path/to/my_project",
      "indexed_at": "2024-04-12T10:00:00Z"
    }
  }
}
```
