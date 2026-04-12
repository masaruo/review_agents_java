import pytest
from src.java_review_agent.agents.aggregator import Aggregator
from src.java_review_agent.schemas.models import ReviewItem, ReviewResult, SlotReviewData, FileReviewData

def test_aggregator_sort_and_unique():
    # 重複する指摘事項
    item1 = ReviewItem(category="BUG", priority=1, location="Line 5", description="NPE", suggestion="Fix")
    item2 = ReviewItem(category="BUG", priority=1, location="Line 5", description="NPE", suggestion="Fix")
    # 優先度が低い指摘事項
    item3 = ReviewItem(category="STYLE", priority=5, location="Line 10", description="Naming", suggestion="Fix")
    
    results = [
        ReviewResult(agent_name="AgentA", items=[item1, item3]),
        ReviewResult(agent_name="AgentB", items=[item2])
    ]
    slot_data = SlotReviewData(slot_id="slot1", results=results)
    file_data = FileReviewData(file_path="App.java", slots=[slot_data])
    
    aggregator = Aggregator()
    aggregated = aggregator.aggregate(file_data)
    
    # 重複除去されているか（item1 と item2 は同じ内容）
    assert len(aggregated.aggregated_items) == 2
    # 優先度順（1 -> 5）にソートされているか
    assert aggregated.aggregated_items[0].priority == 1
    assert aggregated.aggregated_items[1].priority == 5
