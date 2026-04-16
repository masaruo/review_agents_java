from src.java_review_agent.agents.base import BaseReviewAgent

class DesignCritic(BaseReviewAgent):
    @property
    def agent_name(self) -> str:
        return "Design Critic"

    def get_prompt(self, code: str, context: str, custom_instruction: str = "") -> str:
        return f"""You are a software architect specialized in Java design patterns and SOLID principles.
Analyze the following Java code (Java Version: {self.java_version}).

Context:
{context}

Target Code:
{code}

[ADDITIONAL INSTRUCTION FROM USER]
{custom_instruction}

Focus on:
- SOLID principle violations
- Improper use of design patterns
- Tight coupling
- Lack of cohesion
- Extensibility issues

Respond ONLY in JSON format following this schema:
{{
  "items": [
    {{
      "category": "DESIGN",
      "priority": 4,
      "location": "line number or method name",
      "description": "brief description",
      "suggestion": "how to fix"
    }}
  ]
}}
"""
