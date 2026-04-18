import os
import sys
import streamlit as st

# プロジェクトルートを PYTHONPATH に追加
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../"))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import asyncio
from typing import List, Optional
from src.java_review_agent.config import load_config
from src.java_review_agent.backends.ollama import OllamaBackend
from src.java_review_agent.graph import build_graph
from src.java_review_agent.scanner import scan_java_files
from src.java_review_agent.schemas.models import ChatMessage, FileReviewData

# ページ設定
st.set_page_config(page_title="Java Code Review AI Agent", layout="wide")

def initialize_session():
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "last_review" not in st.session_state:
        st.session_state.last_review = None
    if "config" not in st.session_state:
        st.session_state.config = load_config("config.yaml")

def run_review(project_dir: str, custom_instruction: str):
    config = st.session_state.config
    backend = OllamaBackend(config.ollama.base_url)
    
    if not backend.check_connection():
        st.error(f"Could not connect to Ollama at {config.ollama.base_url}")
        return

    app = build_graph(config, backend)
    
    java_files = scan_java_files(project_dir)
    if not java_files:
        st.warning("No Java files found in the specified directory.")
        return

    initial_state = {
        "project_dir": project_dir,
        "java_version": config.java_version,
        "files_to_process": java_files,
        "current_file": None,
        "current_slots": [],
        "all_file_reviews": [],
        "skipped_items": [],
        "custom_instruction": custom_instruction,
        "target_methods": []
    }

    with st.status("Analyzing Java code...", expanded=True) as status:
        st.write(f"Scanning {len(java_files)} files...")
        # グラフの実行 (LangGraph は invoke で同期的にも動く)
        final_state = app.invoke(initial_state)
        status.update(label="Review completed!", state="complete", expanded=False)

    st.session_state.last_review = final_state["all_file_reviews"]
    return final_state["all_file_reviews"]

def format_review_as_markdown(reviews: List[FileReviewData]) -> str:
    md = "# Review Results\n\n"
    for file_review in reviews:
        md += f"## File: `{file_review.file_path}`\n"
        if not file_review.aggregated_items:
            md += "No issues found.\n"
        else:
            for item in file_review.aggregated_items:
                priority_emoji = "🔴" if item.priority >= 4 else "🟡" if item.priority >= 3 else "⚪"
                md += f"### {priority_emoji} [{item.category}] at {item.location}\n"
                md += f"**Description**: {item.description}\n\n"
                md += f"**Suggestion**:\n```java\n{item.suggestion}\n```\n\n"
        md += "---\n"
    return md

def main():
    st.title("☕ Java Code Review AI Agent")
    initialize_session()

    # サイドバー: 設定
    with st.sidebar:
        st.header("Settings")
        project_dir = st.text_input("Project Directory Path", value=os.getcwd())
        custom_instruction = st.text_area("Custom Instruction (Optional)", 
                                          placeholder="e.g., Focus on security vulnerabilities in JPA queries.")
        
        if st.button("Start Review", type="primary"):
            if not os.path.exists(project_dir):
                st.error("Directory does not exist.")
            else:
                reviews = run_review(project_dir, custom_instruction)
                if reviews:
                    # 初回のレポートをチャットにも流す
                    report_md = format_review_as_markdown(reviews)
                    st.session_state.chat_history.append(ChatMessage(role="assistant", content=report_md))

    # メインエリア
    col1, col2 = st.columns([1, 1])

    with col1:
        st.header("📋 Latest Review Report")
        if st.session_state.last_review:
            st.markdown(format_review_as_markdown(st.session_state.last_review))
        else:
            st.info("Run a review from the sidebar to see results here.")

    with col2:
        st.header("💬 AI Assistant")
        # チャット履歴の表示
        for msg in st.session_state.chat_history:
            # レポートは長いので、ここでは最新のレポート以外は折りたたみ表示など工夫の余地があるが、一旦そのまま表示
            with st.chat_message(msg.role):
                st.markdown(msg.content)

        # チャット入力
        if prompt := st.chat_input("Ask about the review results..."):
            st.session_state.chat_history.append(ChatMessage(role="user", content=prompt))
            with st.chat_message("user"):
                st.markdown(prompt)

            # Ollama への問い合わせ
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    config = st.session_state.config
                    backend = OllamaBackend(config.ollama.base_url)
                    
                    # 文脈としてレポートの情報を少し含めるか、あるいは単純にチャットとして送る
                    # ここではシンプルにこれまでの履歴を全部送る（モデルのコンテキスト制限に注意）
                    messages = [{"role": m.role, "content": m.content} for m in st.session_state.chat_history]
                    
                    try:
                        # 履歴を考慮した対話
                        response = backend.chat(config.ollama.model, messages)
                        st.markdown(response)
                        st.session_state.chat_history.append(ChatMessage(role="assistant", content=response))
                    except Exception as e:
                        st.error(f"Error calling AI: {e}")

if __name__ == "__main__":
    main()
