import os
from src.java_review_agent.schemas.models import FileReviewData

class FileReportGenerator:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    def generate(self, file_review: FileReviewData):
        filename = os.path.basename(file_review.file_path)
        report_path = os.path.join(self.output_dir, f"{filename}.md")
        
        content = f"# Code Review Report: {filename}\n\n"
        content += f"**File Path:** `{file_review.file_path}`\n\n"
        
        if not file_review.aggregated_items:
            content += "No issues found.\n"
        else:
            for item in file_review.aggregated_items:
                content += f"## [{item.category}] Priority: {item.priority}\n"
                content += f"**Location:** {item.location}\n\n"
                content += f"### Description\n{item.description}\n\n"
                content += f"### Suggestion\n{item.suggestion}\n\n"
                content += "---\n\n"
        
        with open(report_path, "w") as f:
            f.write(content)
        
        # STDOUT 出力要件
        print(content)
