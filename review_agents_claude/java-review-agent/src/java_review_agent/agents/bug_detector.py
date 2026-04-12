"""Bug Detector — バグ・ロジックエラーの検出（優先度1）"""

from __future__ import annotations

from java_review_agent.agents.base import BaseReviewAgent
from java_review_agent.schemas.models import CodeSlot

_PROMPT_TEMPLATE = """\
You are an expert Java {java_version} code reviewer specializing in bug detection.

Analyze the following Java code and identify bugs, logic errors, and potential runtime exceptions.
Focus on:
- NullPointerException risks
- Resource leaks (unclosed streams, connections)
- Logic errors (off-by-one, incorrect conditions)
- Concurrency issues (race conditions, deadlocks)
- Unhandled exceptions
- Array/collection index out of bounds risks

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
      "priority": 1,
      "category": "bug",
      "severity": "critical|major|minor|info",
      "location": "ClassName#methodName or line description",
      "description": "Clear description of the bug",
      "suggestion": "Specific fix recommendation"
    }}
  ]
}}
"""


class BugDetectorAgent(BaseReviewAgent):
    agent_name: str = "bug_detector"

    def build_prompt(self, slot: CodeSlot, java_version: int) -> str:
        return _PROMPT_TEMPLATE.format(java_version=java_version, code=slot.content)
