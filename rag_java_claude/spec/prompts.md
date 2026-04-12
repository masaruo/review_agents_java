# プロンプトテンプレート仕様書

## 概要

プロンプトは `context_builder.py` の `ContextBuilder` クラスで構築される。
テンプレート変数として `{java_version}`, `{context}`, `{history}`, `{question}` を使用する。

---

## システムプロンプト

```
あなたはJava {java_version}のエキスパートエンジニアです。
提供されたJavaソースコードのコンテキストをもとに、ユーザーの質問に正確かつ詳細に回答してください。

## 回答のガイドライン
- コードに関する説明はMarkdown形式で記述してください
- コードスニペットを示す場合は ```java コードブロック ``` を使用してください
- 不明な点や確認が必要な場合は、正直にその旨を伝えてください
- コンテキストに含まれていない情報について推測する場合は、その旨を明示してください
- バグや問題点を発見した場合は、具体的な修正方法を提示してください
```

---

## ユーザーメッセージテンプレート

```
## コードコンテキスト

{context}

## 会話履歴

{history}

## 質問

{question}
```

---

## コンテキストフォーマットテンプレート

検索された各チャンクは以下のフォーマットで表示される：

```
### ファイル: {file_path}
**クラス**: {class_name}
**メソッド**: {method_name}

**インポート**:
{imports}

**クラスシグネチャ**:
{class_signature}

**メンバー変数**:
{member_vars}

**コード**:
```java
{content}
```

---
```

ファイル全体チャンク（`chunk_type="file"`）の場合：

```
### ファイル: {file_path}
**クラス**: {class_name}

**インポート**:
{imports}

**クラスシグネチャ**:
{class_signature}

**コード**:
```java
{content}
```

---
```

---

## 会話履歴フォーマットテンプレート

```
**ユーザー**: {user_content}

**アシスタント**: {assistant_content}

---
```

履歴が空の場合は `（会話履歴なし）` を表示する。

---

## プロンプト構築ロジック（ContextBuilder）

```python
# 1. コンテキスト文字列を生成
context_str = format_chunks(chunks)

# 2. 履歴文字列を生成
history_str = format_history(history)

# 3. システムプロンプト
system_prompt = SYSTEM_PROMPT.format(java_version=java_version)

# 4. ユーザーメッセージ
user_message = USER_MESSAGE_TEMPLATE.format(
    context=context_str,
    history=history_str,
    question=question,
)

# 5. 最終プロンプト（LLMへの入力）
final_prompt = f"{system_prompt}\n\n{user_message}"

# 6. トークン数チェックと調整
while token_count(final_prompt) > max_input_tokens and history has turns:
    history.remove_oldest_turn()
    # プロンプト再生成
```

---

## トークン制限の適用

| コンポーネント | 優先順位 | 備考 |
|--------------|---------|------|
| システムプロンプト | 最優先（削除しない） | 常に含める |
| コードコンテキスト | 高（削除しない） | 検索結果は常に含める |
| 会話履歴 | 低（古いものから削除） | max_input_tokens超過時に削減 |
| 質問文 | 最低（削除しない） | 常に含める |

トークン計算は `tiktoken` の `cl100k_base` エンコーディングを使用する。
