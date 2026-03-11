# diding-auto (qesg CLI)

AI 에이전트가 Google Workspace를 조작할 수 있는 CLI 도구입니다.
Gmail, Calendar, Drive, Sheets를 터미널 명령어로 제어하고, Claude Code 등 AI에 스킬로 장착할 수 있습니다.

---

## 사전 준비

아래 3가지를 먼저 설치하세요.

### 1. Node.js
https://nodejs.org 에서 LTS 버전 다운로드 → 설치

설치 확인:
```powershell
node --version
```

### 2. Python (3.10 이상)
https://www.python.org/downloads/ 에서 다운로드 → 설치
> 설치 시 **"Add Python to PATH"** 반드시 체크

설치 확인:
```powershell
python --version
```

### 3. Google Cloud CLI (gcloud)
https://cloud.google.com/sdk/docs/install 에서 Windows용 인스톨러 다운로드 → 설치

설치 확인:
```powershell
gcloud --version
```

---

## 설치 방법

### Step 1: 코드 다운로드
```powershell
git clone https://github.com/redchoeng/diding-auto.git
cd diding-auto
```

### Step 2: gws CLI 설치
```powershell
npm install -g @googleworkspace/cli
```

설치 확인:
```powershell
gws --version
```

### Step 3: qesg CLI 설치
```powershell
pip install -e .
```

설치 확인:
```powershell
qesg --version
```

---

## Google 인증 설정

### Step 4: GCP 프로젝트 만들기

1. https://console.cloud.google.com 접속 → 로그인
2. 상단 프로젝트 선택 → **새 프로젝트** 클릭
3. 이름 아무거나 입력 (예: `my-qesg`) → 만들기
4. 터미널에서:
```powershell
gcloud auth login
gcloud config set project [프로젝트ID]
```

### Step 5: API 활성화

터미널에서 아래 명령어 실행:
```powershell
gcloud services enable gmail.googleapis.com calendar-json.googleapis.com drive.googleapis.com sheets.googleapis.com docs.googleapis.com
```

### Step 6: OAuth 동의 화면 설정

1. https://console.cloud.google.com/apis/credentials/consent 접속
2. User Type: **External** 선택 → 만들기
3. 앱 이름: 아무거나 (예: `qesg`)
4. 사용자 지원 이메일: 본인 이메일
5. 개발자 연락처: 본인 이메일
6. **저장 후 계속** 눌러서 끝까지 진행
7. 마지막에 **테스트 사용자** 추가 → 본인 Gmail 주소 입력

> **중요:** 테스트 사용자에 본인 이메일을 추가하지 않으면 로그인이 차단됩니다!

### Step 7: OAuth 클라이언트 ID 만들기

1. https://console.cloud.google.com/apis/credentials 접속
2. **+ 사용자 인증 정보 만들기** → **OAuth 클라이언트 ID**
3. 애플리케이션 유형: **데스크톱 앱**
4. 이름: 아무거나 (예: `qesg`)
5. **만들기** 클릭
6. 나오는 **클라이언트 ID**와 **클라이언트 보안 비밀번호**를 복사

### Step 8: .env 파일 만들기

```powershell
cp .env.example .env
```

`.env` 파일을 열어서 복사한 값을 붙여넣기:
```
GOOGLE_WORKSPACE_CLI_CLIENT_ID=여기에_클라이언트ID_붙여넣기
GOOGLE_WORKSPACE_CLI_CLIENT_SECRET=여기에_클라이언트_시크릿_붙여넣기
```

### Step 9: 구글 계정 로그인

```powershell
$env:GOOGLE_WORKSPACE_CLI_CLIENT_ID = "여기에_클라이언트ID"
$env:GOOGLE_WORKSPACE_CLI_CLIENT_SECRET = "여기에_시크릿"
gws auth login
```

브라우저가 열리면:
1. 구글 계정으로 로그인
2. **계속** 클릭 (경고 무시)
3. 권한 **모두 허용**
4. "인증 성공" 메시지가 나오면 완료

### Step 10: 동작 확인

```powershell
qesg status
qesg mail triage --limit 5
```

메일 목록이 나오면 설치 성공!

---

## 사용법

### 메일

```bash
# 읽지 않은 메일 요약
qesg mail triage --limit 10

# 메일 검색
qesg mail list --query "from:홍길동"

# 특정 메일 읽기
qesg mail read [메일ID]

# 메일 회신 (dry-run으로 미리보기)
qesg mail reply --id [메일ID] --body "확인했습니다." --dry-run

# 새 메일 발송
qesg mail send --to user@gmail.com --subject "안녕하세요" --body "내용입니다"

# 특정인과 대화이력 조회
qesg mail chat --with 홍길동 --topic 프로젝트
```

### 캘린더

```bash
# 오늘 일정
qesg schedule agenda

# 일정 검색
qesg schedule list --query "회의"

# 일정 추가
qesg schedule add --title "팀 회의" --date 2026-03-15 --time 14:00 --duration 1h

# 납품/마감 데드라인 조회
qesg schedule deadlines --days 14 --keyword 납품
```

### Google Drive

```bash
# 파일 검색
qesg doc search "보고서"

# 파일 목록
qesg doc list --type doc

# 로컬 파일을 Drive에 업로드
qesg doc sync --local ./report.md --drive-path "프로젝트" --dry-run
```

### Google Sheets

```bash
# 스프레드시트 검색
qesg data search --query "매출"

# 시트 데이터 읽기
qesg data read [스프레드시트ID] --range "Sheet1!A1:D10"

# 두 시트 비교
qesg data diff --spreadsheet [ID] --sheet1 "시트1" --sheet2 "시트2" --key 종목코드

# 행 추가
qesg data append [ID] --range "Sheet1!A1" --values '["데이터1","데이터2"]'
```

### 레시피 (복합 명령)

```bash
# 아침 루틴: 메일 + 일정 한번에 조회
qesg recipe morning-triage

# 특정인 대화이력 조회
qesg recipe mail-context --person 홍길동
```

### 기타

```bash
# 시스템 상태 확인
qesg status

# AI용 가이드 문서 조회
qesg guide
qesg guide mail
qesg guide data
```

---

## Claude Code 스킬로 등록

AI 에이전트가 직접 조작하게 하려면:

1. 이 파일을 복사:
```powershell
mkdir -p ~/.claude/commands
cp docs/qesg.md ~/.claude/commands/qesg.md
```

2. Claude Code에서 사용:
```
/qesg 오늘 메일 요약해줘
/qesg 김기봉한테 회신 써줘, E16 불가로 사업보고서 대체한다고
/qesg 이번 주 일정 알려줘
/qesg 종목 시트 비교해줘
```

---

## 트러블슈팅

### AhnLab / 백신이 차단하는 경우
gws가 구글 서버에 연결할 때 백신이 차단할 수 있습니다.
→ `node.exe` 또는 gws 설치 경로를 백신 예외에 추가하세요.

### "access_denied" 403 오류
OAuth 동의 화면에서 **테스트 사용자**에 본인 이메일을 추가했는지 확인하세요.
또는 앱을 **프로덕션으로 게시**하면 됩니다.

### PowerShell에서 따옴표 오류
JSON 안의 큰따옴표가 PowerShell에서 문제될 수 있습니다.
→ 큰따옴표를 `""` 두 개로 쓰거나, 작은따옴표 `'`로 감싸세요.

### gws 명령어가 안 되는 경우
```powershell
# PATH에 npm global bin 추가
$env:PATH = "$env:APPDATA\npm;$env:PATH"
gws --version
```

---

## 프로젝트 구조

```
diding-auto/
├── .env.example          # OAuth 설정 템플릿
├── pyproject.toml        # Python 패키지 설정
├── setup_env.ps1         # 원클릭 설치 스크립트
└── qesg/
    ├── cli.py            # 메인 CLI
    ├── core/
    │   ├── config.py     # 설정 관리
    │   ├── gws.py        # gws CLI 래퍼
    │   └── output.py     # JSON 출력
    ├── commands/
    │   ├── mail.py       # Gmail 명령어
    │   ├── schedule.py   # Calendar 명령어
    │   ├── doc.py        # Drive 명령어
    │   ├── data.py       # Sheets 명령어
    │   └── guide.py      # AI용 가이드
    └── recipes/
        └── __init__.py   # 복합 워크플로우
```
