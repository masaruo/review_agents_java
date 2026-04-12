from typing import List, Set, Tuple
from src.java_review_agent.schemas.models import FileReviewData, ReviewItem

class Aggregator:
    def aggregate(self, file_data: FileReviewData) -> FileReviewData:
        all_items: List[ReviewItem] = []
        for slot in file_data.slots:
            for result in slot.results:
                all_items.extend(result.items)
        
        # 重複除去 (category, location, description の組み合わせ)
        unique_items: List[ReviewItem] = []
        seen_keys: Set[Tuple[str, str, str]] = set()
        
        for item in all_items:
            key = (item.category, item.location, item.description)
            if key not in seen_keys:
                unique_items.append(item)
                seen_keys.add(key)
        
        # 優先度順にソート (1が最高)
        unique_items.sort(key=lambda x: x.priority)
        
        file_data.aggregated_items = unique_items
        return file_data
