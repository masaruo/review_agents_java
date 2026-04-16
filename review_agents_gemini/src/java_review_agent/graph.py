from typing import Dict, Any, List
from langgraph.graph import StateGraph, END
from src.java_review_agent.state import GraphState
from src.java_review_agent.scanner import scan_java_files
from src.java_review_agent.agents.preprocessor import Preprocessor
from src.java_review_agent.agents.bug_detector import BugDetector
from src.java_review_agent.agents.security_scanner import SecurityScanner
from src.java_review_agent.agents.efficiency_analyzer import EfficiencyAnalyzer
from src.java_review_agent.agents.design_critic import DesignCritic
from src.java_review_agent.agents.style_reviewer import StyleReviewer
from src.java_review_agent.agents.aggregator import Aggregator
from src.java_review_agent.schemas.models import FileReviewData, SlotReviewData, ReviewResult

import os
from src.java_review_agent.agents.file_report_generator import FileReportGenerator

def build_graph(config: Any, backend: Any):
    # エージェントの初期化
    preprocessor = Preprocessor(chunk_threshold=config.processing.chunk_token_threshold)
    bug_detector = BugDetector(backend, config.ollama.model, config.java_version)
    security_scanner = SecurityScanner(backend, config.ollama.model, config.java_version)
    efficiency_analyzer = EfficiencyAnalyzer(backend, config.ollama.model, config.java_version)
    design_critic = DesignCritic(backend, config.ollama.model, config.java_version)
    style_reviewer = StyleReviewer(backend, config.ollama.model, config.java_version)
    aggregator = Aggregator()
    report_generator = FileReportGenerator(config.output_dir)

    def scanner_node(state: GraphState) -> Dict[str, Any]:
        if state.get("files_to_process"):
            return {}
        files = scan_java_files(state["project_dir"])
        return {"files_to_process": files}

    def preprocessor_node(state: GraphState) -> Dict[str, Any]:
        if not state["files_to_process"]:
            return {"current_file": None}
        
        current_file = state["files_to_process"][0]
        remaining_files = state["files_to_process"][1:]
        
        with open(current_file, "r") as f:
            code = f.read()
        
        slots = preprocessor.preprocess(code)
        return {
            "current_file": current_file,
            "files_to_process": remaining_files,
            "current_slots": slots
        }

    def reviewer_node(state: GraphState) -> Dict[str, Any]:
        if not state["current_file"]:
            return {}
        
        file_review = FileReviewData(file_path=state["current_file"], slots=[])
        
        # シリアル実行要件に基づき、各スロット・各エージェントを順次呼び出す
        for slot in state["current_slots"]:
            slot_data = SlotReviewData(slot_id=slot["slot_id"], results=[])
            
            # 各専門エージェントをシリアルに呼び出し
            agents = [bug_detector, security_scanner, efficiency_analyzer, design_critic, style_reviewer]
            for agent in agents:
                result = agent.review(
                    slot["content"], 
                    slot["context"], 
                    custom_instruction=state.get("custom_instruction", "")
                )
                slot_data.results.append(result)
                
                if "skipped" in result.status:
                    state["skipped_items"].append({
                        "file": state["current_file"],
                        "slot": slot["slot_id"],
                        "agent": agent.agent_name,
                        "reason": result.status
                    })
            
            file_review.slots.append(slot_data)
        
        # 集約
        file_review = aggregator.aggregate(file_review)
        
        # レポート生成
        report_generator.generate(file_review)
        
        return {
            "all_file_reviews": state["all_file_reviews"] + [file_review]
        }

    def summary_node(state: GraphState) -> Dict[str, Any]:
        # サマリーレポート生成（簡易版）
        summary_path = os.path.join(config.output_dir, "summary.md")
        content = "# Project Review Summary\n\n"
        content += f"**Processed Files:** {len(state['all_file_reviews'])}\n"
        content += f"**Skipped Items:** {len(state['skipped_items'])}\n\n"
        
        if state["skipped_items"]:
            content += "## Skipped Items\n\n"
            for item in state["skipped_items"]:
                content += f"- File: `{item['file']}`, Agent: `{item['agent']}`, Reason: `{item['reason']}`\n"
        
        with open(summary_path, "w") as f:
            f.write(content)
        
        print("\n=== Summary ===\n")
        print(content)
        
        return {}

    workflow = StateGraph(GraphState)
    workflow.add_node("scanner", scanner_node)
    workflow.add_node("preprocess", preprocessor_node)
    workflow.add_node("review", reviewer_node)
    workflow.add_node("summary", summary_node)

    workflow.set_entry_point("scanner")
    workflow.add_edge("scanner", "preprocess")
    workflow.add_edge("preprocess", "review")
    
    # ループ判定
    workflow.add_conditional_edges(
        "review",
        lambda state: "preprocess" if state["files_to_process"] else "summary",
        {
            "preprocess": "preprocess",
            "summary": "summary"
        }
    )
    workflow.add_edge("summary", END)

    return workflow.compile()
