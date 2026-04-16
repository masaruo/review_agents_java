import os
import sys
import argparse
from src.java_review_agent.config import load_config
from src.java_review_agent.backends.ollama import OllamaBackend
from src.java_review_agent.graph import build_graph

def parse_args(args=None):
    parser = argparse.ArgumentParser(description="Java Code Review AI Agent")
    parser.add_argument("dir", help="Project directory to review")
    parser.add_argument("--config", default="config.yaml", help="Path to config.yaml")
    parser.add_argument("--files", nargs="+", help="Specific files to review")
    parser.add_argument("--instruction", help="Custom review instruction")
    return parser.parse_args(args)

def main():
    args = parse_args()

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
        "skipped_items": [],
        "custom_instruction": args.instruction,
        "target_methods": [] # 今後の拡張用
    }

    # files_to_process を初期化
    from src.java_review_agent.scanner import scan_java_files
    initial_state["files_to_process"] = scan_java_files(args.dir, target_files=args.files)

    if not initial_state["files_to_process"]:
        print("No Java files found to process.")
        return

    print(f"Starting review for {len(initial_state['files_to_process'])} file(s) in: {args.dir}")
    if args.instruction:
        print(f"Custom instruction: {args.instruction}")

    app.invoke(initial_state)
    print("Review completed.")

if __name__ == "__main__":
    main()
