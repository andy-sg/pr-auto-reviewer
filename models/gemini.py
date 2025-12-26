"""Gemini AI model implementation using Vertex AI."""
from vertexai.generative_models import GenerativeModel
import vertexai
from models.base import BaseModel
from typing import Dict, Any
from config import Config
import json


class GeminiModel(BaseModel):
    """Gemini AI model implementation using Vertex AI."""

    def __init__(self):
        # Initialize Vertex AI
        vertexai.init(
            project=Config.VERTEX_AI_PROJECT_ID,
            location=Config.VERTEX_AI_LOCATION
        )
        self.model = GenerativeModel("gemini-3-pro-preview")

    def review_code(
        self,
        file_path: str,
        patch: str,
        file_content: str,
        pr_context: Dict[str, Any]
    ) -> list[Dict[str, Any]]:
        """Review code changes and generate review comments."""
        prompt = f"""당신은 전문 코드 리뷰어입니다. 다음 코드 변경사항을 검토하고 건설적인 피드백을 제공하세요.

PR 컨텍스트:
- 제목: {pr_context.get('title', 'N/A')}
- 설명: {pr_context.get('description', 'N/A')}

파일: {file_path}

Git Diff (변경사항):
```diff
{patch}
```

변경 후 전체 파일 내용:
```
{file_content}
```

## 리뷰 우선순위 가이드라인

**CRITICAL (🔴 필수 수정)** - 반드시 수정해야 하는 심각한 문제:
- 명확한 버그나 런타임 에러
- 보안 취약점 (SQL injection, XSS, 인증 누락 등)
- 데이터 손실 가능성
- 메모리 누수나 심각한 성능 문제
- null/undefined 참조 에러
- 무한 루프나 데드락

**MAJOR (🟡 권장 수정)** - 가능하면 수정해야 하는 중요한 문제:
- 잠재적 버그 (edge case 처리 누락)
- 잘못된 로직이나 알고리즘
- 중요한 에러 처리 누락
- 심각한 코드 중복
- 성능에 영향을 주는 비효율적인 코드
- API 사용 오류
- 타입 안정성 문제

**MINOR (⚪️ 참고용)** - 시간이 되면 개선하면 좋은 사항:
- 변수/함수 네이밍 개선
- 코드 스타일 통일
- 사소한 리팩토링
- 주석 추가/개선
- 작은 가독성 개선

**중요 지침**:
- CRITICAL과 MAJOR 이슈에 집중하세요
- MINOR 이슈는 정말 명확하고 쉽게 개선 가능한 경우에만 포함하세요
- 각 severity에 맞는 이모지를 사용하세요: 🔴(critical), 🟡(major), ⚪️(minor)

각 코멘트에는 반드시 다음 내용을 포함하세요:
1. Severity 레벨과 이모지
2. 문제점 설명
3. 구체적인 수정 방법 (코드 예시 포함)
4. 수정 이유

JSON 형식으로 리뷰 코멘트 배열을 응답하세요:
[
  {{
    "body": "🔴 **CRITICAL**\n\n**문제점**: [문제 설명]\n\n**수정 방법**:\n```language\n[수정된 코드 예시]\n```\n\n**이유**: [수정 이유]",
    "line": 새_파일의_라인_번호,
    "side": "RIGHT",
    "severity": "critical"
  }}
]

코멘트 예시:

🔴 CRITICAL 예시:
{{
  "body": "🔴 **CRITICAL**\n\n**문제점**: null 체크 없이 객체 속성에 접근하여 런타임 에러가 발생할 수 있습니다.\n\n**수정 방법**:\n```python\nif user and user.name:\n    print(user.name)\nelse:\n    print('Unknown user')\n```\n\n**이유**: null/undefined 접근은 애플리케이션 크래시를 유발합니다.",
  "line": 42,
  "side": "RIGHT",
  "severity": "critical"
}}

🟡 MAJOR 예시:
{{
  "body": "🟡 **MAJOR**\n\n**문제점**: 에러가 발생해도 처리되지 않아 사용자에게 적절한 피드백이 제공되지 않습니다.\n\n**수정 방법**:\n```python\ntry:\n    result = risky_operation()\nexcept ValueError as e:\n    logger.error(f'Operation failed: {{e}}')\n    return {{'error': 'Invalid input'}}\n```\n\n**이유**: 에러 처리는 안정적인 서비스 제공에 필수적입니다.",
  "line": 58,
  "side": "RIGHT",
  "severity": "major"
}}

⚪️ MINOR 예시:
{{
  "body": "⚪️ **MINOR**\n\n**문제점**: 변수명 'data'가 너무 포괄적이어서 의미를 파악하기 어렵습니다.\n\n**수정 방법**:\n```python\nuser_data = fetch_user()  # 더 명확한 변수명\n```\n\n**이유**: 명확한 변수명은 코드의 의도를 쉽게 파악할 수 있게 합니다.",
  "line": 12,
  "side": "RIGHT",
  "severity": "minor"
}}

문제가 없으면 빈 배열을 반환하세요: []
실제로 변경되었거나 변경사항과 직접 관련된 라인에만 코멘트하세요.
모든 코멘트는 한국어로 작성하세요.
"""

        response = self.model.generate_content(prompt)
        result_text = response.text

        # Try to extract JSON from the response
        try:
            # Find JSON array in the response
            start_idx = result_text.find('[')
            end_idx = result_text.rfind(']') + 1
            if start_idx != -1 and end_idx > start_idx:
                json_str = result_text[start_idx:end_idx]
                return json.loads(json_str)
            else:
                return []
        except json.JSONDecodeError:
            return []

    def analyze_review(
        self,
        file_content: str,
        file_path: str,
        review_comment: str,
        pr_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze review comment and determine needed changes."""
        prompt = f"""You are a code review assistant. Analyze this review comment and determine what changes need to be made.

PR Context:
- Title: {pr_context.get('title', 'N/A')}
- Description: {pr_context.get('description', 'N/A')}

File: {file_path}
Review Comment: {review_comment}

Current File Content:
```
{file_content}
```

Analyze the review and respond in JSON format with:
{{
    "action": "modify|create|delete|no_action",
    "reasoning": "explanation of what needs to be done",
    "changes": ["list of specific changes to make"]
}}
"""

        response = self.model.generate_content(prompt)
        result_text = response.text

        # Try to extract JSON from the response
        try:
            # Find JSON in the response
            start_idx = result_text.find('{')
            end_idx = result_text.rfind('}') + 1
            if start_idx != -1 and end_idx > start_idx:
                json_str = result_text[start_idx:end_idx]
                return json.loads(json_str)
            else:
                return {
                    "action": "no_action",
                    "reasoning": "Could not parse response",
                    "changes": []
                }
        except json.JSONDecodeError:
            return {
                "action": "no_action",
                "reasoning": "Could not parse response",
                "changes": []
            }

    def generate_code_fix(
        self,
        file_content: str,
        file_path: str,
        review_comment: str,
        line_number: int = None
    ) -> str:
        """Generate fixed code based on review."""
        line_info = f"at line {line_number}" if line_number else ""

        prompt = f"""You are a code review assistant. Fix the code based on this review comment.

File: {file_path} {line_info}
Review Comment: {review_comment}

Current File Content:
```
{file_content}
```

Please provide the COMPLETE fixed file content. Return ONLY the fixed code without any explanation or markdown formatting.
"""

        response = self.model.generate_content(prompt)
        fixed_code = response.text.strip()

        # Remove markdown code blocks if present
        if fixed_code.startswith('```'):
            lines = fixed_code.split('\n')
            # Remove first line (```language)
            lines = lines[1:]
            # Remove last line (```)
            if lines[-1].strip() == '```':
                lines = lines[:-1]
            fixed_code = '\n'.join(lines)

        return fixed_code

    def generate_reply(
        self,
        review_comment: str,
        changes_made: str
    ) -> str:
        """Generate a reply to the review comment."""
        prompt = f"""Generate a brief, professional reply to this code review comment.

Review Comment: {review_comment}
Changes Made: {changes_made}

Generate a short reply (1-2 sentences) acknowledging the feedback and confirming the changes.
Keep it professional and concise. Do not use markdown formatting.
"""

        response = self.model.generate_content(prompt)
        return response.text.strip()
