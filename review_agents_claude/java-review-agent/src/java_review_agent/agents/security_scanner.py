"""Security Scanner — セキュリティ脆弱性の検出（優先度2）"""

from __future__ import annotations

from java_review_agent.agents.base import BaseReviewAgent
from java_review_agent.schemas.models import CodeSlot

_PROMPT_TEMPLATE = """\
You are an expert Java {java_version} security auditor.

Analyze the following Java code and identify security vulnerabilities.
Focus on:
- SQL injection
- Command injection
- Cross-site scripting (XSS) risks
- Improper authentication or authorization
- Exposure of sensitive information (passwords, tokens, PII in logs)
- Insecure random number generation
- Weak or insecure cryptography
- Deserialization vulnerabilities
- Path traversal risks

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
      "priority": 2,
      "category": "security",
      "severity": "critical|major|minor|info",
      "location": "ClassName#methodName or line description",
      "description": "Clear description of the security issue",
      "suggestion": "Specific remediation recommendation"
    }}
  ]
}}
"""


class SecurityScannerAgent(BaseReviewAgent):
    agent_name: str = "security_scanner"

    def build_prompt(self, slot: CodeSlot, java_version: int) -> str:
        return _PROMPT_TEMPLATE.format(java_version=java_version, code=slot.content)
