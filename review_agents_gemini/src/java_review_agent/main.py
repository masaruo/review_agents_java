import os
import sys
import argparse
from src.java_review_agent.config import load_config
from src.java_review_agent.backends.ollama import OllamaBackend
from src.java_review_agent.graph import build_graph

def main():
    parser = argparse.ArgumentParser(description="Java Code Review AI Agent")
    parser.add_argument("dir", help="Project directory to review")
    parser.add_argument("--config", default="config.yaml", help="Path to config.yaml")
    args = parser.parse_args()

    # 設定読み込み
    try:
        config = load_config(args.config)
    except Exception as e:
        print(f"Error loading config: {e}", file=sys.stderr)
        sys.exit(1)

    # Ollama 接続確認
    backend = OllamaBackend(config.ollama.base_url)
    if not backend.check_connection():
        print(f"Error: Could not connect to Ollama at {config.ollama.base_url}", file=sys.stderr)
        print("Please ensure Ollama is running and the model is available.", file=sys.stderr)
        sys.exit(1)

    # グラフ構築と実行
    app = build_graph(config, backend)
    
    initial_state = {
        "project_dir": args.dir,
        "java_version": config.java_version,
        "files_to_process": [],
        "current_file": None,
        "current_slots": [],
        "all_file_reviews": [],
        "skipped_items": []
    }

    print(f"Starting review for directory: {args.dir}")
    app.invoke(initial_state)
    print("Review completed.")

if __name__ == "__main__":
    main()
