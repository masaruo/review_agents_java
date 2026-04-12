"""Efficiency Analyzer — アルゴリズム・I/O効率の分析（優先度3）"""

from __future__ import annotations

from java_review_agent.agents.base import BaseReviewAgent
from java_review_agent.schemas.models import CodeSlot

_PROMPT_TEMPLATE = """\
You are an expert Java {java_version} performance engineer.

Analyze the following Java code and identify efficiency issues.
Focus on:
- Inefficient algorithms (O(n^2) or worse where better is possible)
- Inappropriate data structure choices
- Unnecessary object creation in loops
- Database or I/O calls inside loops
- Inefficient string concatenation (should use StringBuilder)
- Missing caching opportunities
- Unnecessary synchronization

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
      "priority": 3,
      "category": "efficiency",
      "severity": "critical|major|minor|info",
      "location": "ClassName#methodName or line description",
      "description": "Clear description of the efficiency issue",
      "suggestion": "Specific optimization recommendation"
    }}
  ]
}}
"""


class EfficiencyAnalyzerAgent(BaseReviewAgent):
    agent_name: str = "efficiency_analyzer"

    def build_prompt(self, slot: CodeSlot, java_version: int) -> str:
        return _PROMPT_TEMPLATE.format(java_version=java_version, code=slot.content)
