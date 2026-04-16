"""グラフ状態の初期化ヘルパー"""

from __future__ import annotations

from java_review_agent.schemas.models import Config, ReviewGraphState, ReviewInstruction


def initial_state(
    project_dir: str,
    config: Config,
    review_instruction: ReviewInstruction | None = None,
) -> ReviewGraphState:
    """ReviewGraphState の初期値を生成する"""
    return ReviewGraphState(
        project_dir=project_dir,
        java_version=config.java_version,
        config=config,
        review_instruction=review_instruction or ReviewInstruction(),
        java_files=[],
        current_file_index=0,
        current_file_path="",
        slots=[],
        current_slot_index=0,
        slot_agent_outputs=[],
        aggregated_result=None,
        file_reports=[],
        skipped_items=[],
        summary_content=None,
        fatal_error=None,
    )
