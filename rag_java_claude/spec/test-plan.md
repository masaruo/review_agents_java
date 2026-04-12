# テスト計画書

## テスト方針

- **TDD（テスト駆動開発）**: テストを先に書き、テストが通るように実装する
- **モック使用**: Ollama、ChromaDBへの実際の接続はモックする
- **フィクスチャ**: `tests/fixtures/sample_java/` にテスト用Javaファイルを配置する
- **テスト分離**: 各テストは独立して実行可能であること

---

## テストファイル構成

```
tests/
├── __init__.py
├── unit/
│   ├── __init__.py
│   ├── test_schemas.py         # Pydanticモデルテスト
│   ├── test_config.py          # 設定読み込みテスト
│   ├── test_chunker.py         # チャンキングテスト
│   ├── test_indexer.py         # IndexerおよびFileScannerテスト
│   ├── test_retriever.py       # Retrieverテスト
│   ├── test_context_builder.py # ContextBuilderテスト
│   ├── test_chat_session.py    # ChatSessionテスト
│   ├── test_project_manager.py # ProjectManagerテスト
│   └── test_error_handling.py  # エラーハンドリングテスト
├── integration/
│   ├── __init__.py
│   └── test_rag_chain.py       # RAGチェーン統合テスト
└── fixtures/
    └── sample_java/
        ├── Calculator.java
        └── UserService.java
```

---

## テストケース詳細

### 1. スキーマテスト（test_schemas.py）

#### 1.1 AppConfig
- `test_app_config_default_values`: デフォルト値が正しいこと
- `test_app_config_from_dict`: dict から生成できること
- `test_ollama_config_validation`: OllamaConfig のバリデーション
- `test_rag_config_validation`: RagConfig のバリデーション
- `test_storage_config_validation`: StorageConfig のバリデーション

#### 1.2 ChunkMetadata
- `test_chunk_metadata_creation`: 正しく生成できること
- `test_chunk_metadata_default_values`: デフォルト値が正しいこと
- `test_chunk_type_validation`: chunk_type が "method" または "file" であること

#### 1.3 JavaChunk
- `test_java_chunk_creation`: 正しく生成できること
- `test_java_chunk_serialization`: JSON シリアライゼーションが正しいこと

#### 1.4 ConversationTurn / ChatHistory
- `test_conversation_turn_creation`: role と content が正しく設定されること
- `test_chat_history_add_turn`: ターン追加が機能すること
- `test_chat_history_truncate`: 古いターンが正しく削除されること

#### 1.5 ProjectRegistry
- `test_project_registry_empty`: 空のレジストリが正しく生成されること
- `test_project_registry_add_project`: プロジェクト追加が機能すること
- `test_project_registry_serialization`: JSON シリアライゼーションが正しいこと

---

### 2. 設定読み込みテスト（test_config.py）

- `test_load_config_from_yaml_string`: YAML文字列から設定を読み込めること
- `test_default_config_when_no_file`: ファイルなしでデフォルト値が使われること
- `test_config_singleton`: `get_config()` が同じインスタンスを返すこと
- `test_env_override_ollama_base_url`: 環境変数 `OLLAMA_BASE_URL` で上書きできること

---

### 3. チャンキングテスト（test_chunker.py）

#### 3.1 インポート抽出
- `test_extract_imports_from_calculator`: `Calculator.java` からインポートを正しく抽出できること
- `test_extract_imports_from_user_service`: `UserService.java` からインポートを正しく抽出できること
- `test_extract_imports_empty`: インポートなしのファイルで空リストを返すこと

#### 3.2 クラスシグネチャ抽出
- `test_extract_class_signature_public`: `public class` シグネチャを正しく抽出できること
- `test_extract_class_signature_with_extends`: `extends` を含むシグネチャを抽出できること

#### 3.3 メンバー変数抽出
- `test_extract_member_vars_from_calculator`: `Calculator.java` のメンバー変数を正しく抽出できること
- `test_extract_member_vars_private`: `private` メンバー変数を抽出できること
- `test_extract_member_vars_empty`: メンバー変数なしで空リストを返すこと

#### 3.4 メソッド分割
- `test_chunk_calculator_methods`: `Calculator.java` を5つのメソッドチャンクに分割できること
  - `add`, `subtract`, `multiply`, `divide`, `getHistory`
- `test_chunk_metadata_attached`: 各チャンクにメタデータが正しく付与されていること
- `test_chunk_type_method`: メソッドチャンクの `chunk_type` が "method" であること

#### 3.5 ファイル全体チャンク
- `test_small_file_as_single_chunk`: 1000トークン未満のファイルが1チャンクになること
- `test_chunk_type_file`: ファイル全体チャンクの `chunk_type` が "file" であること

#### 3.6 エッジケース
- `test_large_file_split_by_method`: 大きいファイルがメソッド単位に分割されること
- `test_file_with_no_methods`: メソッドなしのファイルが全体チャンクになること

---

### 4. IndexerおよびFileScannerテスト（test_indexer.py）

#### 4.1 FileScanner
- `test_scan_returns_only_java_files`: `.java` ファイルのみを返すこと
- `test_scan_recursive`: サブディレクトリも再帰的にスキャンすること
- `test_scan_empty_directory`: 空ディレクトリで空リストを返すこと
- `test_scan_nonexistent_directory`: 存在しないディレクトリで `FileNotFoundError` を発生させること
- `test_scan_no_java_files`: `.java` ファイルがない場合に空リストを返すこと

#### 4.2 Indexer（モック使用）
- `test_indexer_calls_embedder_with_batch`: エンベディングがバッチで呼ばれること
- `test_indexer_full_rebuild_deletes_first`: 既存コレクションを全削除してから挿入すること
- `test_indexer_returns_chunk_count`: インデックスされたチャンク数を返すこと
- `test_indexer_empty_project`: `.java` ファイルが0件の場合に0を返すこと

---

### 5. Retrieverテスト（test_retriever.py）

- `test_retriever_returns_top_k_results`: top_k 件の結果を返すこと
- `test_retriever_results_include_score`: 結果にスコアが含まれること
- `test_retriever_empty_index_returns_empty`: 空のインデックスで空リストを返すこと
- `test_retriever_index_not_found_raises_error`: インデックス未構築で `IndexNotFoundError` を発生させること

---

### 6. ContextBuilderテスト（test_context_builder.py）

- `test_context_builder_combines_chunks_and_history`: チャンクと履歴が正しく結合されること
- `test_context_builder_empty_history`: 履歴が空でもプロンプトが生成されること
- `test_context_builder_empty_chunks`: チャンクが空でもプロンプトが生成されること
- `test_context_builder_truncates_history_when_over_limit`: max_input_tokens超過時に古い履歴が削除されること
- `test_context_builder_token_counting_accurate`: トークンカウントが正確であること
- `test_context_builder_question_not_truncated`: 質問文が切り詰められないこと

---

### 7. ChatSessionテスト（test_chat_session.py）

- `test_chat_session_maintains_history`: 複数ターンで履歴が保持されること
- `test_chat_session_history_truncated_to_max`: max_history_turns を超えると古い履歴が削除されること
- `test_chat_session_exits_on_exit_command`: "exit" 入力でループが終了すること
- `test_chat_session_exits_on_quit_command`: "quit" 入力でループが終了すること

---

### 8. ProjectManagerテスト（test_project_manager.py）

- `test_register_new_project`: 新規プロジェクトが正しく登録されること
- `test_register_updates_existing_project`: 既存プロジェクト名で登録すると `updated_at` が更新されること
- `test_get_registered_project`: 登録済みプロジェクトを取得できること
- `test_get_unknown_project_raises_error`: 未登録プロジェクトで `ProjectNotFoundError` を発生させること
- `test_get_unknown_project_error_includes_list`: エラーメッセージに登録済みリストが含まれること
- `test_delete_project_removes_from_registry`: 削除後にレジストリから除外されること
- `test_delete_project_removes_index_directory`: 削除後にインデックスディレクトリが削除されること
- `test_delete_unknown_project_raises_error`: 未登録プロジェクトで `ProjectNotFoundError` を発生させること
- `test_list_projects_returns_all`: 全プロジェクトのリストを返すこと
- `test_list_projects_empty`: プロジェクトなしで空リストを返すこと

---

### 9. エラーハンドリングテスト（test_error_handling.py）

- `test_ollama_connection_failure`: Ollama未起動時に適切なエラーが発生すること
- `test_model_not_found`: モデル未取得時に適切なエラーが発生すること
- `test_embedding_model_not_found`: エンベディングモデル未取得時に適切なエラーが発生すること
- `test_index_not_found`: インデックス未構築時に `IndexNotFoundError` が発生すること
- `test_unknown_project_in_chat`: 未登録プロジェクトでchatを開始するとエラーになること
- `test_llm_parse_error_continues_session`: LLMパースエラー時にセッションが継続されること

---

### 10. RAGチェーン統合テスト（test_rag_chain.py）

- `test_index_retrieve_generate_produces_answer`: インデックス→検索→生成の一連のフローが正しく動作すること（全モック）
- `test_multi_turn_second_question_has_context`: マルチターンで2問目に1問目の文脈が引き継がれること

---

### 11. トークン制限テスト

`test_context_builder.py` 内に含める：

- `test_truncation_when_max_input_tokens_exceeded`: `max_input_tokens` 超過時に切り詰められること
- `test_oldest_history_removed_first`: 最古の履歴から削除されること
- `test_system_prompt_not_truncated`: システムプロンプトは削除されないこと
- `test_context_chunks_not_truncated`: コードコンテキストは削除されないこと

---

### 12. エッジケーステスト

#### `test_indexer.py` 内：
- `test_empty_project_directory`: 空のプロジェクトディレクトリ（`.java` ファイルなし）
- `test_no_src_directory`: `src/` ディレクトリが存在しない場合

#### `test_chunker.py` 内：
- `test_extremely_large_file`: 極端に大きいファイルがクラッシュしないこと
- `test_file_with_no_methods`: メソッドなしのJavaファイル

---

## テスト環境

### フィクスチャ

`tests/fixtures/sample_java/Calculator.java`:
- `add`, `subtract`, `multiply`, `divide`, `getHistory` の5メソッドを持つ
- メンバー変数: `private int result;`, `private List<Integer> history;`
- インポート: `java.util.List`, `java.util.ArrayList`

`tests/fixtures/sample_java/UserService.java`:
- `createUser`, `findById`, `findAll`, `deleteUser` の4メソッドを持つ
- インポート: `com.example.model.User`, `com.example.repository.UserRepository` など

### モック戦略

| コンポーネント | モック方法 |
|--------------|---------|
| OllamaLLM | `unittest.mock.MagicMock` で `generate()` を差し替え |
| OllamaEmbedding | `unittest.mock.MagicMock` で `embed()` を差し替え（固定ベクトルを返す） |
| ChromaDB | `unittest.mock.MagicMock` でコレクションを差し替え |
| ファイルシステム | `pytest` の `tmp_path` フィクスチャを使用 |

### 実行コマンド
```bash
# 全テスト
make test

# 特定ファイル
uv run pytest tests/unit/test_chunker.py -v

# カバレッジ付き
uv run pytest --cov=src/java_qa_agent tests/

# 特定カテゴリ
uv run pytest tests/unit/ -v
uv run pytest tests/integration/ -v
```
