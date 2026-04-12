"""Style Reviewer — 可読性・コーディング規約の大まかな評価（優先度5）"""

from __future__ import annotations

from java_review_agent.agents.base import BaseReviewAgent
from java_review_agent.schemas.models import CodeSlot

_PROMPT_TEMPLATE = """\
You are an expert Java {java_version} code reviewer focusing on readability.

Analyze the following Java code and identify significant readability issues.
IMPORTANT: Do NOT enumerate every minor style violation. Only report major readability concerns that
significantly impact code understanding or maintainability.
Focus on:
- Unclear or misleading naming (variables, methods, classes)
- Methods that are too long or complex (high cyclomatic complexity)
- Missing or inadequate documentation for public APIs
- Deep nesting that makes code hard to follow
- Inconsistent code style that is notably jarring

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
      "priority": 5,
      "category": "style",
      "severity": "critical|major|minor|info",
      "location": "ClassName#methodName or line description",
      "description": "Clear description of the readability issue",
      "suggestion": "Specific improvement recommendation"
    }}
  ]
}}
"""


class StyleReviewerAgent(BaseReviewAgent):
    agent_name: str = "style_reviewer"

    def build_prompt(self, slot: CodeSlot, java_version: int) -> str:
        return _PROMPT_TEMPLATE.format(java_version=java_version, code=slot.content)
