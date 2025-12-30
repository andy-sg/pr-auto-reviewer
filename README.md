# PR Auto Reviewer

GitHub PR의 리뷰 코멘트를 읽고, AI로 코드를 자동 수정한 후 커밋/푸시하고 답변을 달아주는 CLI 도구입니다.

## 기능

- PR 리뷰 코멘트 자동 수집
- AI(Gemini)를 이용한 코드 자동 수정
- 수정할 코멘트 선택 기능
- 답변 미리보기 및 수정 기능
- Git 커밋/푸시 자동화
- 한국어 답변 생성

## 설치

```bash
# 의존성 설치
npm install

# 빌드
npm run build

# 전역 설치 (선택사항)
npm link
```

## 설정

`.env` 파일을 생성하고 다음 값을 설정하세요:

```env
# GitHub Personal Access Token
GITHUB_TOKEN=github_pat_xxxxx

# Vertex AI (for Gemini)
VERTEX_AI_PROJECT_ID=your-gcp-project-id
VERTEX_AI_LOCATION=us-central1

# Model Selection
DEFAULT_MODEL=gemini
```

### GCP 인증

Gemini 모델을 사용하려면 GCP 인증이 필요합니다:

```bash
gcloud auth application-default login
```

## 사용법

```bash
# 기본 사용
pr-fix https://github.com/owner/repo/pull/123

# 특정 레포지토리 경로 지정
pr-fix https://github.com/owner/repo/pull/123 --repo-path /path/to/repo

# 미리보기 모드 (실제 변경 없음)
pr-fix https://github.com/owner/repo/pull/123 --dry-run

# 자동 답변 비활성화
pr-fix https://github.com/owner/repo/pull/123 --no-auto-reply
```

### 개발 모드

```bash
# tsx로 직접 실행 (빌드 없이)
npm run dev https://github.com/owner/repo/pull/123
```

## 옵션

| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `--repo-path <path>` | 대상 레포지토리 경로 | `.` |
| `--dry-run` | 실제 변경 없이 미리보기 | `false` |
| `--no-auto-reply` | 자동 답변 비활성화 | `false` |

## 워크플로우

1. PR URL에서 리뷰 코멘트 수집
2. 코멘트 목록 표시
3. 처리 방식 선택 (모두 처리 / 선택 처리 / 취소)
4. 각 코멘트에 대해 AI로 코드 수정
5. 생성된 답변 미리보기 및 수정/확인
6. Git 커밋 및 푸시
7. GitHub에 답변 게시

## 프로젝트 구조

```
pr-auto-reviewer/
├── src/
│   ├── index.ts         # CLI 진입점
│   ├── config.ts        # 설정 관리
│   ├── types.ts         # 타입 정의
│   ├── github-client.ts # GitHub API (Octokit)
│   ├── code-modifier.ts # AI 코드 수정
│   ├── git-ops.ts       # Git 작업
│   └── models/
│       ├── base.ts      # AI 모델 인터페이스
│       ├── gemini.ts    # Gemini 구현
│       └── index.ts     # 모델 팩토리
├── dist/                # 빌드 결과물
├── package.json
├── tsconfig.json
└── .env
```

## 라이선스

MIT
