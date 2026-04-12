"""LangGraph グラフ定義 — ノード・エッジ・遷移条件"""

from __future__ import annotations

from typing import Any

from langgraph.graph import END, START, StateGraph

from java_review_agent.agents.aggregator import aggregate
from java_review_agent.agents.bug_detector import BugDetectorAgent
from java_review_agent.agents.design_critic import DesignCriticAgent
from java_review_agent.agents.efficiency_analyzer import EfficiencyAnalyzerAgent
from java_review_agent.agents.file_report_generator import generate_file_report
from java_review_agent.agents.preprocessor import preprocess_file
from java_review_agent.agents.security_scanner import SecurityScannerAgent
from java_review_agent.agents.style_reviewer import StyleReviewerAgent
from java_review_agent.agents.summary_generator import SummaryGeneratorAgent
from java_review_agent.backends.ollama import OllamaBackend
from java_review_agent.scanner import scan_java_files
from java_review_agent.schemas.models import Config, ReviewGraphState


def build_graph(config: Config) -> Any:
    """
    LangGraph グラフを構築して返す。
    各ノードはシリアルに実行される（LangGraphの並列Send APIは使用しない）。

    Args:
        config: 設定モデル

    Returns:
        compiled LangGraph app
    """
    backend = OllamaBackend(
        base_url=config.ollama.base_url,
        model=config.ollama.model,
        timeout_seconds=config.ollama.timeout_seconds,
    )

    agents = [
        BugDetectorAgent(backend),
        SecurityScannerAgent(backend),
        EfficiencyAnalyzerAgent(backend),
        DesignCriticAgent(backend),
        StyleReviewerAgent(backend),
    ]

    summary_agent = SummaryGeneratorAgent(backend)

    # ─── ノード定義 ───────────────────────────────────────────

    def node_file_scanner(state: ReviewGraphState) -> dict:
        java_files = scan_java_files(state["project_dir"])
        return {
            "java_files": java_files,
            "current_file_index": 0,
        }

    def node_preprocessor(state: ReviewGraphState) -> dict:
        idx = state["current_file_index"]
        file_path = state["java_files"][idx]
        cfg = state["config"]

        slots, skipped = preprocess_file(
            file_path=file_path,
            chunk_token_threshold=cfg.processing.chunk_token_threshold,
            max_input_tokens=cfg.processing.max_input_tokens,
        )

        existing_skipped = list(state.get("skipped_items", []))
        return {
            "current_file_path": file_path,
            "slots": slots,
            "current_slot_index": 0,
            "slot_agent_outputs": [],
            "skipped_items": existing_skipped + skipped,
        }

    def node_review_agents(state: ReviewGraphState) -> dict:
        """全レビューエージェントをスロットごとにシリアル実行する"""
        slots = state["slots"]
        java_version = state["java_version"]
        existing_outputs = list(state.get("slot_agent_outputs", []))
        existing_skipped = list(state.get("skipped_items", []))

        new_outputs = []
        new_skipped = []

        for slot in slots:
            for agent in agents:
                output, skipped_items = agent.review(slot, java_version)
                new_outputs.append(output)
                new_skipped.extend(skipped_items)

        return {
            "slot_agent_outputs": existing_outputs + new_outputs,
            "skipped_items": existing_skipped + new_skipped,
        }

    def node_aggregator(state: ReviewGraphState) -> dict:
        aggregated, _ = aggregate(
            agent_outputs=state["slot_agent_outputs"],
            file_path=state["current_file_path"],
        )
        # スキップはreview_agentsノードで既に追加済み
        return {"aggregated_result": aggregated}

    def node_file_report(state: ReviewGraphState) -> dict:
        cfg = state["config"]
        report = generate_file_report(
            aggregated=state["aggregated_result"],
            output_dir=cfg.output.dir,
        )
        existing_reports = list(state.get("file_reports", []))
        return {
            "file_reports": existing_reports + [report],
            "current_file_index": state["current_file_index"] + 1,
        }

    def node_summary(state: ReviewGraphState) -> dict:
        cfg = state["config"]
        content = summary_agent.generate(
            file_reports=state["file_reports"],
            skipped_items=state.get("skipped_items", []),
            java_version=state["java_version"],
            project_dir=state["project_dir"],
            output_dir=cfg.output.dir,
        )
        return {"summary_content": content}

    # ─── ルーティング ──────────────────────────────────────────

    def route_after_scanner(state: ReviewGraphState) -> str:
        if not state["java_files"]:
            return END
        return "preprocessor"

    def route_after_file_report(state: ReviewGraphState) -> str:
        idx = state["current_file_index"]
        total = len(state["java_files"])
        if idx < total:
            return "preprocessor"
        return "summary"

    # ─── グラフ組み立て ────────────────────────────────────────

    graph = StateGraph(ReviewGraphState)

    graph.add_node("file_scanner", node_file_scanner)
    graph.add_node("preprocessor", node_preprocessor)
    graph.add_node("review_agents", node_review_agents)
    graph.add_node("aggregator", node_aggregator)
    graph.add_node("file_report", node_file_report)
    graph.add_node("summary", node_summary)

    graph.add_edge(START, "file_scanner")
    graph.add_conditional_edges("file_scanner", route_after_scanner)
    graph.add_edge("preprocessor", "review_agents")
    graph.add_edge("review_agents", "aggregator")
    graph.add_edge("aggregator", "file_report")
    graph.add_conditional_edges("file_report", route_after_file_report)
    graph.add_edge("summary", END)

    return graph.compile()
