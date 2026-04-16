from src.java_review_agent.agents.base import BaseReviewAgent

class EfficiencyAnalyzer(BaseReviewAgent):
    @property
    def agent_name(self) -> str:
        return "Efficiency Analyzer"

    def get_prompt(self, code: str, context: str, custom_instruction: str = "") -> str:
        return f"""You are a performance engineer specializing in Java.
Analyze the following Java code (Java Version: {self.java_version}).

Context:
{context}

Target Code:
{code}

[ADDITIONAL INSTRUCTION FROM USER]
{custom_instruction}

Focus on:
- Inefficient algorithms or data structures
- Unnecessary object creation
- I/O efficiency
- Memory management
- Performance bottlenecks

Respond ONLY in JSON format following this schema:
{{
  "items": [
    {{
      "category": "EFFICIENCY",
      "priority": 3,
      "location": "line number or method name",
      "description": "brief description",
      "suggestion": "how to fix"
    }}
  ]
}}
"""
