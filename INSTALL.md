# PR Auto Reviewer 설치 가이드

팀원들을 위한 설치 및 사용 가이드입니다.

## 방법 1: Git에서 직접 설치 (권장)

### 1. 저장소 클론

```bash
git clone <repository-url>
cd pr-auto-reviewer
```

### 2. 패키지 설치

```bash
# pip로 설치
pip install -e .

# 또는 uv 사용 (더 빠름)
uv pip install -e .
```

### 3. 환경 변수 설정

`.env` 파일을 만들고 필요한 API 키를 설정하세요:

```bash
cp .env.example .env
# .env 파일을 편집하여 API 키 입력
```

필요한 API 키:
- `GITHUB_TOKEN`: GitHub Personal Access Token (repo 권한 필요)
- `ANTHROPIC_API_KEY`: Claude API 키 (선택)
- `VERTEX_AI_PROJECT_ID`: Google Cloud 프로젝트 ID (선택)
- `VERTEX_AI_LOCATION`: Google Cloud 리전 (선택)

### 4. 사용

설치 후 어디서든 `pr-reviewer` 명령어 사용 가능:

```bash
# 기본 사용법 (인터랙티브 모드)
pr-reviewer https://github.com/owner/repo/pull/123 --mode review

# Severity 레벨 직접 지정
pr-reviewer https://github.com/owner/repo/pull/123 --mode review --min-severity major

# 특정 모델 사용
pr-reviewer https://github.com/owner/repo/pull/123 --mode review --model claude
```

## 방법 2: 패키지 빌드 후 배포

### 패키지 빌드

```bash
# 빌드 도구 설치
pip install build

# 패키지 빌드
python -m build
```

`dist/` 폴더에 `.whl` 파일이 생성됩니다.

### 팀원 설치

생성된 `.whl` 파일을 팀원들에게 공유:

```bash
pip install pr_auto_reviewer-0.1.0-py3-none-any.whl
```

## 인터랙티브 Severity 선택

`--min-severity` 옵션 없이 실행하면 체크박스로 선택 가능:

```bash
pr-reviewer https://github.com/owner/repo/pull/123 --mode review
```

```
어떤 severity 레벨의 코멘트를 포함할까요?
❯ ◉ 🔴 CRITICAL (필수 수정: 버그, 보안 취약점 등)
  ◉ 🟡 MAJOR (권장 수정: 잠재적 버그, 에러 처리 누락 등)
  ◯ ⚪️ MINOR (참고용: 네이밍, 스타일 등)
```

- **Space**: 선택/해제
- **Enter**: 확인
- **a**: 전체 선택

## 사용 가능한 옵션

```bash
pr-reviewer --help
```

주요 옵션:
- `--mode review`: PR 리뷰 모드
- `--mode fix`: 리뷰 코멘트 자동 수정 모드
- `--model claude|gemini|claude-code`: AI 모델 선택
- `--min-severity critical|major|minor`: Severity 레벨 필터
- `--dry-run`: 실제 변경 없이 미리보기

## Severity 레벨 설명

### 🔴 CRITICAL (필수 수정)
- 명확한 버그나 런타임 에러
- 보안 취약점 (SQL injection, XSS 등)
- 데이터 손실 가능성
- 메모리 누수

### 🟡 MAJOR (권장 수정)
- 잠재적 버그 (edge case 처리 누락)
- 중요한 에러 처리 누락
- 성능 문제
- API 사용 오류

### ⚪️ MINOR (참고용)
- 변수/함수 네이밍 개선
- 코드 스타일
- 사소한 리팩토링
- 주석 추가

## 문제 해결

### 설치 오류
```bash
# Python 버전 확인 (3.9 이상 필요)
python --version

# 의존성 재설치
pip install -e . --force-reinstall
```

### API 키 오류
- `.env` 파일이 올바른 위치에 있는지 확인
- API 키가 유효한지 확인
- GitHub Token의 권한 확인 (repo 스코프 필요)

## 업데이트

```bash
# Git에서 최신 코드 가져오기
git pull

# 의존성 업데이트
pip install -e . --upgrade
```
