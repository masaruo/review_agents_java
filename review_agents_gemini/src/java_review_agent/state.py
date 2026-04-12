from typing import List, Optional, Dict, Any, TypedDict
from src.java_review_agent.schemas.models import FileReviewData

class GraphState(TypedDict):
    project_dir: str
    java_version: int
    files_to_process: List[str]
    current_file: Optional[str]
    current_slots: List[Dict[str, Any]]
    all_file_reviews: List[FileReviewData]
    skipped_items: List[Dict[str, Any]]
