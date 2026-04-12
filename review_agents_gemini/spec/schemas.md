# Schemas Specification

## 1. Pydantic モデル定義

### ReviewItem
各エージェントが生成する個別の指摘事項。
```python
class ReviewItem(BaseModel):
    category: str  # BUG, SECURITY, EFFICIENCY, DESIGN, STYLE
    priority: int  # 1-5
    location: str  # line number or method name
    description: str
    suggestion: str
```

### ReviewResult
1つのスロット（メソッドまたはファイル全体）に対するエージェントの出力。
```python
class ReviewResult(BaseModel):
    agent_name: str
    items: List[ReviewItem]
    status: str = "success"  # success, skipped (resource limit), skipped (parse error)
```

### SlotReviewData
1つのチャンク（スロット）に対する全エージェントのレビュー結果。
```python
class SlotReviewData(BaseModel):
    slot_id: str
    results: List[ReviewResult]
```

### FileReviewData
1つの Java ファイルに対する全スロットの結果。
```python
class FileReviewData(BaseModel):
    file_path: str
    slots: List[SlotReviewData]
    aggregated_items: List[ReviewItem] = []
```

### GraphState
LangGraph の状態定義。
```python
class GraphState(TypedDict):
    project_dir: str
    java_version: int
    files_to_process: List[str]
    current_file: Optional[str]
    current_slots: List[Dict[str, Any]]
    all_file_reviews: List[FileReviewData]
    skipped_items: List[Dict[str, Any]]
```

## 2. Aggregator スキーマ
Aggregator は `FileReviewData` を入力とし、`aggregated_items` を埋めて出力する。
重複除去は `category`, `location`, `description` の類似度に基づいて行う。

## 3. Config スキーマ
`config.yaml` のバリデーション用。
```python
class OllamaConfig(BaseModel):
    base_url: str
    model: str
    timeout_seconds: int

class ProcessingConfig(BaseModel):
    max_concurrency: int
    chunk_token_threshold: int
    max_input_tokens: int
    response_reserve_tokens: int

class AppConfig(BaseModel):
    java_version: int
    ollama: OllamaConfig
    processing: ProcessingConfig
    output_dir: str
```
