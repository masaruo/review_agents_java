"""Design Critic — 設計パターン・SOLID原則の評価（優先度4）"""

from __future__ import annotations

from java_review_agent.agents.base import BaseReviewAgent
from java_review_agent.schemas.models import CodeSlot

_PROMPT_TEMPLATE = """\
You are an expert Java {java_version} software architect.

Analyze the following Java code and identify design issues.
Focus on:
- SOLID principle violations:
  - Single Responsibility Principle (SRP)
  - Open/Closed Principle (OCP)
  - Liskov Substitution Principle (LSP)
  - Interface Segregation Principle (ISP)
  - Dependency Inversion Principle (DIP)
- Inappropriate design pattern usage
- High coupling, low cohesion
- Poor testability
- God classes or methods

Java Version: {java_version}

Code:
```java
{code}
```

Respond ONLY in the following JSON format. Do not add any explanation outside the JSON.
If no issues are found, return an empty "issues" array.

{{
  "issues": [
    {{
      "priority": 4,
      "category": "design",
      "severity": "critical|major|minor|info",
      "location": "ClassName#methodName or line description",
      "description": "Clear description of the design issue",
      "suggestion": "Specific refactoring recommendation"
    }}
  ]
}}
"""


class DesignCriticAgent(BaseReviewAgent):
    agent_name: str = "design_critic"

    def build_prompt(self, slot: CodeSlot, java_version: int) -> str:
        return _PROMPT_TEMPLATE.format(java_version=java_version, code=slot.content)
