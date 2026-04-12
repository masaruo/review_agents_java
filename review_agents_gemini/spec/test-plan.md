# Test Plan Specification

## 1. テスト戦略
本プロジェクトは TDD (Test-Driven Development) に基づいて進行する。まずテストを作成し、それをパスするように実装を行う。

## 2. テストカテゴリとケース

### 単体テスト (Unit Tests)
- **Preprocessor**:
    - トークン数推定が正確か
    - 1,000トークン超のファイルが正しくメソッド単位に分割されるか
    - 各スロットに正しいコンテキスト（インポート、クラス情報）が付与されるか
- **Review Agents**:
    - 各エージェントが Pydantic モデルに従った結果を生成するか（モック LLM 使用）
- **Aggregator**:
    - 優先度順のソートが正しいか
    - 重複した指摘事項が正しく除去されるか
- **Scanner**:
    - `src/` 以下の `.java` ファイルを正しく列挙できるか

### スキーマテスト (Schema Tests)
- Pydantic モデルのバリデーションが有効か
- 不正な LLM 出力に対するパースエラー処理が機能するか

### グラフ遷移テスト (Graph Integration Tests)
- LangGraph の状態遷移がファイルスキャンからサマリー生成まで期待通りに進むか
- シリアル実行の制御（逐次的なノード呼び出し）が担保されているか

### 統合テスト (Integration Tests)
- **Ollama 接続**: Ollama サーバーとの通信が成立するか
- **エンドツーエンド**: サンプル Java プロジェクトに対して、レポートが `review_output/` に生成されるか

### エラーハンドリングテスト
- **Ollama 未起動**: 起動時にエラーを出力して即時終了するか
- **OOM / Timeout**: 特定のファイルでエラーが発生しても、スキャン全体が停止せずに `Skipped` として記録されるか
- **空ファイル / 巨大ファイル**: 正常に処理またはスキップされるか

### 回帰テスト (Regression Tests)
- 既知のバグパターン（NullPointerException 等）を含む Java ファイルに対して、Bug Detector が正しく指摘を行うか

## 3. テスト環境
- `pytest` と `pytest-asyncio` を使用。
- Ollama の呼び出しは必要に応じてモック化するが、一部の統合テストでは実際のローカル Ollama を使用する。
- フィクスチャとして、様々なパターンの `.java` ファイルを `tests/fixtures/sample_java/` に配置する。
