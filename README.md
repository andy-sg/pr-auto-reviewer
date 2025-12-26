# PR Auto Reviewer

🤖 AI 기반 GitHub Pull Request 자동 리뷰 및 수정 도구

**두 가지 모드 지원:**
- 🔍 **Review Mode**: AI가 PR 코드를 분석하고 한국어로 리뷰 댓글 작성
- 🔧 **Fix Mode**: 리뷰 댓글을 읽고 자동으로 코드 수정 및 커밋/푸시

📖 **[설치 가이드](INSTALL.md)** | **[아키텍처 문서](ARCHITECTURE.md)**

---

## 📋 목차

- [주요 기능](#주요-기능)
- [빠른 시작](#빠른-시작)
- [Review Mode 사용법](#review-mode-사용법)
- [Fix Mode 사용법](#fix-mode-사용법)
- [Severity 레벨](#severity-레벨)
- [팀 배포](#팀-배포)
- [설정](#설정)
- [트러블슈팅](#트러블슈팅)

---

## 주요 기능

### 🔍 Review Mode

**✨ 새로운 기능들:**
- ⚡ **병렬 리뷰**: 최대 5개 파일을 동시에 리뷰하여 속도 10배 향상
- 🇰🇷 **한국어 리뷰**: 모든 코멘트가 한국어로 작성되며 구체적인 수정 방법 포함
- 🎯 **Severity 레벨**: CRITICAL/MAJOR/MINOR로 이슈 우선순위 구분
- ✅ **인터랙티브 선택**: 체크박스로 리뷰할 severity 레벨 선택
- 🔍 **MINOR 이슈 필터**: MINOR 이슈는 개별적으로 검토하고 선택 가능
- 🛡️ **라인 검증**: GitHub API 422 에러 방지를 위한 자동 라인 번호 검증

**리뷰 항목:**
1. 🐛 버그 및 런타임 에러
2. 🔒 보안 취약점
3. ⚡ 성능 문제
4. 📚 코드 품질 및 베스트 프랙티스
5. 🔧 유지보수성

### 🔧 Fix Mode

- GitHub PR 리뷰 댓글 자동 분석
- AI를 사용한 코드 자동 수정
- Git 커밋 및 푸시 자동화
- 리뷰 댓글에 자동 답변

### 🎯 지원 AI 모델

- **Claude** (권장) - Anthropic API
- **Claude Code** - CLI 기반, API 키 불필요
- **Gemini** - Google Cloud Vertex AI

---

## 빠른 시작

### 1. 설치

```bash
# 저장소 클론
git clone <repository-url>
cd pr-auto-reviewer

# uv 설치 (없는 경우)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 의존성 설치
uv sync
```

### 2. 환경 변수 설정

```bash
cp .env.example .env
# .env 파일 편집하여 API 키 입력
```

필수 설정:
```env
# GitHub Personal Access Token (필수)
GITHUB_TOKEN=your_github_token_here

# Claude API 키 (선택 - Claude 모델 사용 시)
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

### 3. 실행

```bash
# AI가 PR 리뷰 작성 (인터랙티브)
python main.py https://github.com/owner/repo/pull/123 --mode review

# 리뷰 댓글 자동 수정
python main.py https://github.com/owner/repo/pull/123 --mode fix
```

---

## Review Mode 사용법

### 기본 사용

```bash
# 인터랙티브 모드 (권장)
python main.py <PR_URL> --mode review

# Severity 레벨 직접 지정
python main.py <PR_URL> --mode review --min-severity major

# Dry run으로 미리보기
python main.py <PR_URL> --mode review --dry-run
```

### 인터랙티브 워크플로우

#### 1단계: Severity 레벨 선택
```
어떤 severity 레벨의 코멘트를 포함할까요?
❯ ◉ 🔴 CRITICAL (필수 수정: 버그, 보안 취약점 등)
  ◉ 🟡 MAJOR (권장 수정: 잠재적 버그, 에러 처리 누락 등)
  ◯ ⚪️ MINOR (참고용: 네이밍, 스타일 등)
```

- **Space**: 선택/해제
- **Enter**: 확인
- 기본값: CRITICAL + MAJOR 선택됨

#### 2단계: 병렬 리뷰 실행
```
AI Code Review Mode
Severity 필터: 🔴 CRITICAL + 🟡 MAJOR

Reviewing 5 file(s) in parallel...

✓ main.py: 2 suggestion(s) (filtered from 8)
✓ config.py: 1 suggestion(s) (filtered from 3)
✓ utils.py: No issues found
```

#### 3단계: MINOR 이슈 개별 선택 (MINOR 포함 시)
```
⚪️ MINOR 이슈 5개가 발견되었습니다.
각 이슈를 확인하고 포함할 항목을 선택하세요.

MINOR 이슈 중 포함할 항목을 선택하세요:
  ◯ main.py:42 - ⚪️ **MINOR** 변수명 'data'가 너무 포괄적...
  ◯ config.py:15 - ⚪️ **MINOR** 함수명이 명확하지 않음...
  ◯ utils.py:89 - ⚪️ **MINOR** 주석이 부족합니다...
```

#### 4단계: GitHub에 리뷰 포스팅
```
✓ 2개의 MINOR 이슈가 선택되었습니다.

Posting review with 5 comment(s)...
✓ Review posted successfully!
```

### 리뷰 코멘트 형식

AI가 작성하는 한국어 리뷰 예시:

```markdown
🔴 **CRITICAL**

**문제점**: null 체크 없이 객체 속성에 접근하여 런타임 에러가 발생할 수 있습니다.

**수정 방법**:
```python
if user and user.name:
    print(user.name)
else:
    print('Unknown user')
```

**이유**: null/undefined 접근은 애플리케이션 크래시를 유발합니다.
```

---

## Fix Mode 사용법

### 기본 사용

```bash
# 기본 (Fix Mode는 기본값)
python main.py <PR_URL>

# 명시적 지정
python main.py <PR_URL> --mode fix

# 자동 댓글 답변 비활성화
python main.py <PR_URL> --mode fix --no-auto-reply

# 저장소 경로 지정
python main.py <PR_URL> --mode fix --repo-path /path/to/repo
```

### 워크플로우

1. PR의 리뷰 댓글 가져오기
2. 각 댓글 분석 및 수정사항 결정
3. 코드 자동 수정
4. Git 커밋 및 푸시
5. 리뷰 댓글에 답변 작성

### 출력 예시

```
Auto-Fix Mode

Found 3 review comment(s)

Comment 1/3
File: src/main.py
Line: 45
Comment: Please add error handling...
✓ Successfully applied fix

Committing and pushing changes...
✓ Committed and pushed changes

Summary
Successful: 3
Failed: 0
```

---

## Severity 레벨

### 🔴 CRITICAL (필수 수정)
**반드시 수정해야 하는 심각한 문제**
- 명확한 버그나 런타임 에러
- 보안 취약점 (SQL injection, XSS 등)
- 데이터 손실 가능성
- 메모리 누수
- null/undefined 참조 에러
- 무한 루프나 데드락

### 🟡 MAJOR (권장 수정)
**가능하면 수정해야 하는 중요한 문제**
- 잠재적 버그 (edge case 처리 누락)
- 잘못된 로직이나 알고리즘
- 중요한 에러 처리 누락
- 성능에 영향을 주는 비효율적인 코드
- API 사용 오류
- 타입 안정성 문제

### ⚪️ MINOR (참고용)
**시간이 되면 개선하면 좋은 사항**
- 변수/함수 네이밍 개선
- 코드 스타일 통일
- 사소한 리팩토링
- 주석 추가/개선
- 작은 가독성 개선

### Severity 필터링

```bash
# CRITICAL만
python main.py <PR_URL> --mode review --min-severity critical

# CRITICAL + MAJOR (기본값)
python main.py <PR_URL> --mode review --min-severity major

# 모든 레벨 (MINOR 포함)
python main.py <PR_URL> --mode review --min-severity minor

# 인터랙티브 선택 (옵션 없이 실행)
python main.py <PR_URL> --mode review
```

---

## 팀 배포

### 패키지 빌드

```bash
# uv로 빌드
uv build

# dist/ 폴더에 생성됨
# - pr_auto_reviewer-0.1.0-py3-none-any.whl
# - pr_auto_reviewer-0.1.0.tar.gz
```

### 팀원 설치 방법

#### 방법 1: Git에서 직접 설치 (권장)
```bash
git clone <repository-url>
cd pr-auto-reviewer

# pip 또는 uv로 설치
pip install -e .
# 또는
uv pip install -e .

# 환경 변수 설정
cp .env.example .env
# .env 편집
```

#### 방법 2: Wheel 파일 배포
```bash
# 빌드된 wheel 파일 공유
pip install pr_auto_reviewer-0.1.0-py3-none-any.whl
# 또는
uv pip install pr_auto_reviewer-0.1.0-py3-none-any.whl
```

설치 후 `pr-reviewer` 명령어 사용 가능:
```bash
pr-reviewer <PR_URL> --mode review
```

자세한 내용은 **[INSTALL.md](INSTALL.md)** 참고

---

## 설정

### 환경 변수 (.env)

```env
# 필수: GitHub Personal Access Token
# 권한: repo, write:discussion
GITHUB_TOKEN=your_github_token_here

# 선택: AI 모델 API 키
ANTHROPIC_API_KEY=your_anthropic_api_key_here
VERTEX_AI_PROJECT_ID=your_gcp_project_id
VERTEX_AI_LOCATION=us-central1

# 기본 모델 선택
DEFAULT_MODEL=claude
```

### GitHub Token 생성

1. GitHub Settings → Developer settings → Personal access tokens
2. Generate new token (classic)
3. 권한 선택:
   - ✅ `repo` (전체)
   - ✅ `write:discussion`

### 지원 AI 모델

| 모델 | API 키 | 설정 방법 |
|------|--------|-----------|
| **Claude** | 필요 | `ANTHROPIC_API_KEY` 설정 |
| **Claude Code** | 불필요 | `claude auth login` |
| **Gemini** | 필요 | GCP 인증 + `VERTEX_AI_PROJECT_ID` |

---

## 명령어 옵션

### 전체 옵션

```bash
python main.py <PR_URL> [OPTIONS]

Options:
  --mode [review|fix]              모드 선택 (기본: fix)
  --model [claude|claude-code|gemini]  AI 모델 선택
  --min-severity [critical|major|minor]  Severity 필터 (review 모드)
  --repo-path PATH                 로컬 저장소 경로 (기본: .)
  --auto-reply / --no-auto-reply   자동 댓글 답변 (기본: true)
  --dry-run                        실제 변경 없이 확인만
  --help                           도움말 표시
```

### 사용 예시

```bash
# Review Mode
python main.py <PR_URL> --mode review
python main.py <PR_URL> --mode review --min-severity critical
python main.py <PR_URL> --mode review --model claude
python main.py <PR_URL> --mode review --dry-run

# Fix Mode
python main.py <PR_URL>
python main.py <PR_URL> --mode fix
python main.py <PR_URL> --mode fix --no-auto-reply
python main.py <PR_URL> --mode fix --repo-path /path/to/repo

# 패키지 설치 후
pr-reviewer <PR_URL> --mode review
```

---

## 프로젝트 구조

```
pr-auto-reviewer/
├── main.py              # CLI 엔트리포인트
├── config.py            # 설정 관리
├── github_client.py     # GitHub API (라인 검증 포함)
├── code_reviewer.py     # 코드 리뷰 로직
├── code_modifier.py     # 코드 수정 로직
├── git_ops.py          # Git 작업 자동화
├── models/             # AI 모델 구현
│   ├── base.py         # 추상 인터페이스
│   ├── claude.py       # Claude API
│   ├── claude_code.py  # Claude Code CLI
│   └── gemini.py       # Gemini (Vertex AI)
├── pyproject.toml      # 패키징 설정
├── README.md           # 이 문서
├── INSTALL.md          # 설치 가이드
└── ARCHITECTURE.md     # 아키텍처 문서
```

---

## 트러블슈팅

### GitHub API 422 에러

**문제:** `Unprocessable Entity: 422 Line could not be resolved`

**해결:** 이제 자동으로 해결됩니다! 라인 번호를 자동 검증하여 유효하지 않은 라인은 필터링합니다.

### GitHub 권한 에러

**문제:** `401 Unauthorized`

**해결:**
```bash
# 1. 토큰 확인
echo $GITHUB_TOKEN

# 2. 토큰 권한 확인
# GitHub Settings → Personal access tokens
# repo, write:discussion 확인
```

### 리뷰가 느림

**해결:** 이제 자동으로 병렬 처리됩니다! 최대 5개 파일을 동시에 리뷰하여 10배 빠릅니다.

### MINOR 이슈가 너무 많음

**해결:**
```bash
# 1. MINOR 제외
python main.py <PR_URL> --mode review --min-severity major

# 2. 인터랙티브 선택
python main.py <PR_URL> --mode review
# → 체크박스에서 MINOR 해제

# 3. MINOR 개별 선택
python main.py <PR_URL> --mode review --min-severity minor
# → 각 MINOR 이슈를 검토하고 선택
```

---

## FAQ

**Q: Review Mode와 Fix Mode를 함께 사용할 수 있나요?**
A: 네! Review Mode로 먼저 리뷰한 후, Fix Mode로 자동 수정할 수 있습니다.

**Q: 리뷰가 한국어로만 작성되나요?**
A: 네, 모든 리뷰 코멘트가 한국어로 작성됩니다. 문제점, 수정 방법, 이유를 명확하게 제시합니다.

**Q: MINOR 이슈를 모두 제외하려면?**
A: `--min-severity major` 옵션을 사용하거나, 인터랙티브 체크박스에서 MINOR를 해제하세요.

**Q: 팀원들에게 어떻게 배포하나요?**
A: `uv build`로 wheel 파일을 생성하여 공유하거나, Git 저장소에서 `pip install -e .`로 설치하세요. [INSTALL.md](INSTALL.md) 참고

**Q: 리뷰가 너무 오래 걸려요**
A: 이제 병렬 처리로 자동 최적화됩니다. 5개 파일을 동시에 리뷰합니다.

**Q: wheel 파일의 none-any는 무엇인가요?**
A: 순수 Python 패키지라는 의미입니다. 모든 OS(Windows, macOS, Linux)에서 같은 파일로 사용 가능합니다.

---

## 주요 업데이트

### v0.1.0 (최신)
- ⚡ 병렬 리뷰로 10배 속도 향상
- 🇰🇷 한국어 리뷰 코멘트
- 🎯 Severity 레벨 시스템 (CRITICAL/MAJOR/MINOR)
- ✅ 인터랙티브 체크박스 선택
- 🔍 MINOR 이슈 개별 선택
- 🛡️ GitHub 422 에러 자동 해결
- 📦 패키징 및 팀 배포 지원

---

## 라이선스

MIT

---

## 기여

이슈 및 PR 환영합니다!

**개발 가이드:**
- 코드 스타일: PEP 8
- 타입 힌트 사용 권장
- 새 기능은 테스트와 함께 제출

**문의:**
- Issues: GitHub Issues 사용
- 기능 제안: Discussion 탭 활용
