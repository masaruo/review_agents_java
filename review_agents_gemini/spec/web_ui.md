# SPEC: Streamlit Web UI

## 1. 目的
CLIでの一括処理に加え、ブラウザ上でJavaコードのレビュー実行およびAIとの対話（チャット）を行えるようにする。

## 2. UI構成（業務用スタイル）
Streamlitを使用し、サイドバーとメインエリアで構成する。

### サイドバー (設定・入力)
- **Project Directory**: レビュー対象のディレクトリパス入力。
- **Configuration**: `config.yaml` の設定表示（読み取り専用または簡易変更）。
- **Execution Button**: 「レビュー開始」ボタン。

### メインエリア (出力・対話)
- **Status Container**: 現在の処理ステップ（スキャン中、解析中など）のプログレス表示。
- **Report Display**: 生成されたレビュー結果（Markdown）の表示。
- **Chat Interface**: 
    - レビュー結果に対する追加質問。
    - Ollama (qwen2.5-coder) との継続的な対話。

## 3. アーキテクチャ
- **Frontend**: Streamlit
- **Backend**: `src.java_review_agent.graph.build_graph` を再利用。
- **State Management**: `st.session_state` を使用して、レビュー結果と会話履歴を保持。

## 4. データフロー
1. ユーザーがディレクトリパスを入力し「レビュー開始」をクリック。
2. `app.invoke(initial_state)` が走り、結果が `st.session_state.last_review` に保存される。
3. 画面にレビュー結果が表示される。
4. ユーザーがチャット入力欄に質問を書くと、`st.session_state.history` に追加され、LLMが回答を生成する。

## 5. 制限事項
- ローカル環境での利用を前提とする（ディレクトリパスはサーバー実行環境の絶対パス）。
- ファイルアップロード機能ではなく、既存のディレクトリ指定を優先する。
