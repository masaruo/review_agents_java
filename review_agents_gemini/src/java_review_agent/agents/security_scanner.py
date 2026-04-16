from src.java_review_agent.agents.base import BaseReviewAgent

class SecurityScanner(BaseReviewAgent):
    @property
    def agent_name(self) -> str:
        return "Security Scanner"

    def get_prompt(self, code: str, context: str, custom_instruction: str = "") -> str:
        return f"""You are a security expert specializing in Java applications.
Analyze the following Java code (Java Version: {self.java_version}).

Context:
{context}

Target Code:
{code}

[ADDITIONAL INSTRUCTION FROM USER]
{custom_instruction}

Focus on:
- SQL/OS Injection
- Improper authentication/authorization
- Exposure of sensitive information
- Hardcoded secrets
- Use of insecure libraries

Respond ONLY in JSON format following this schema:
{{
  "items": [
    {{
      "category": "SECURITY",
      "priority": 2,
      "location": "line number or method name",
      "description": "brief description",
      "suggestion": "how to fix"
    }}
  ]
}}
"""
