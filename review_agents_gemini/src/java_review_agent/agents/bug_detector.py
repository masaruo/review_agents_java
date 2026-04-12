from src.java_review_agent.agents.base import BaseReviewAgent

class BugDetector(BaseReviewAgent):
    @property
    def agent_name(self) -> str:
        return "Bug Detector"

    def get_prompt(self, code: str, context: str) -> str:
        return f"""You are an expert Java developer specialized in finding bugs and logic errors.
Analyze the following Java code (Java Version: {self.java_version}).

Context:
{context}

Target Code:
{code}

Focus on:
- NullPointerException
- Resource leaks
- Logic errors
- Boundary conditions
- Race conditions (if applicable)

Respond ONLY in JSON format following this schema:
{{
  "items": [
    {{
      "category": "BUG",
      "priority": 1,
      "location": "line number or method name",
      "description": "brief description of the bug",
      "suggestion": "how to fix it"
    }}
  ]
}}
"""
