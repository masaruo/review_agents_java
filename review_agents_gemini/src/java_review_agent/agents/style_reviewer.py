from src.java_review_agent.agents.base import BaseReviewAgent

class StyleReviewer(BaseReviewAgent):
    @property
    def agent_name(self) -> str:
        return "Style Reviewer"

    def get_prompt(self, code: str, context: str, custom_instruction: str = "") -> str:
        return f"""You are a senior Java developer who values readability and clean code.
Analyze the following Java code (Java Version: {self.java_version}).

Context:
{context}

Target Code:
{code}

[ADDITIONAL INSTRUCTION FROM USER]
{custom_instruction}

Focus on:
- General readability
- Coding conventions (summary level only)
- Meaningful naming
- Method length and complexity
- Comments and documentation

Respond ONLY in JSON format following this schema:
{{
  "items": [
    {{
      "category": "STYLE",
      "priority": 5,
      "location": "line number or method name",
      "description": "brief description",
      "suggestion": "how to fix"
    }}
  ]
}}
"""
