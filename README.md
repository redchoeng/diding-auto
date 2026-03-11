# QESG — AI 업무 자동화 비서

Google Workspace(Gmail, Calendar, Drive, Sheets)를 AI로 자동화하는 데스크톱 앱 + CLI 도구입니다.

> **두 가지 사용 방법:** 데스크톱 앱(`qesg-app`)으로 GUI 사용 또는 터미널(`qesg`)로 CLI 사용

---

## 한눈에 보기

| 기능 | 설명 |
|------|------|
| AI 비서 | 자연어로 메일 요약, 일정 확인, 회신 초안 작성 |
| 메일 | 읽지 않은 메일 조회, 검색, 대화이력, AI 회신 초안 |
| 캘린더 | 오늘 일정, 데드라인 확인, 일정 추가 |
| Drive | 파일 검색, 목록 조회 |
| Sheets | 스프레드시트 검색, 데이터 읽기 |
| LLM 지원 | Gemini / Claude / OpenAI 선택 가능 |

---

## 사전 준비

아래 3가지를 먼저 설치하세요.

### 1. Node.js
https://nodejs.org 에서 LTS 버전 다운로드 → 설치

```powershell
node --version
```

### 2. Python (3.10 이상)
https://www.python.org/downloads/ 에서 다운로드 → 설치
> 설치 시 **"Add Python to PATH"** 반드시 체크

```powershell
python --version
```

### 3. Google Cloud CLI (gcloud)
https://cloud.google.com/sdk/docs/install 에서 Windows용 인스톨러 다운로드 → 설치

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

### Step 3: qesg 설치

**기본 설치 (CLI + 데스크톱 앱):**
```powershell
pip install -e .
```

**AI 비서 기능까지 사용하려면:**
```powershell
pip install -e ".[llm]"
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

## 데스크톱 앱 사용법

### 실행

```powershell
qesg-app
```

앱이 실행되면 왼쪽 사이드바에서 원하는 기능을 선택합니다.

---

### AI 비서 탭

자연어로 업무를 처리하는 AI 챗봇입니다.

**빠른 실행 버튼:**
| 버튼 | 기능 |
|------|------|
| 메일 요약 | 읽지 않은 메일을 발신자별로 그룹핑해서 요약 |
| 오늘 일정 | 오늘 캘린더 일정 조회 |
| 데드라인 | 이번 주 마감/납품 데드라인 확인 |
| 아침 루틴 | 메일 요약 + 일정을 한번에 조회 |

**직접 입력 예시:**
```
홍길동한테 온 메일 요약해줘
내일 회의 일정 잡아줘
김부장님한테 회신 써줘, 3월 15일에 미팅 가능하다고
이번 달 납품 일정 정리해줘
```

> 처음 사용 시 **설정 탭**에서 LLM API 키를 먼저 입력해야 합니다.

---

### 메일 탭

**읽지 않은 메일 조회:**
1. **읽지 않은 메일** 버튼 클릭
2. 발신자별로 그룹핑되어 표시됨
3. 각 발신자 옆 버튼:
   - 시계 아이콘 → 해당 발신자와의 **대화이력** 조회
   - 연필 아이콘 → AI가 **회신 초안** 작성

**메일 검색:**
1. 검색어 입력 (예: `from:홍길동`, `subject:보고서`)
2. **검색** 버튼 클릭

**대화이력 조회:**
1. 이름 입력 (예: `홍길동`)
2. 주제 입력 (선택, 예: `프로젝트`)
3. **조회** 버튼 클릭

**AI 회신 초안:**
1. 메일 목록에서 발신자 옆 연필 아이콘 클릭
2. 회신 방향 입력 (예: "일정 확인했고 3월 15일 가능하다고")
3. **AI 초안 생성** 클릭
4. 생성된 초안을 복사해서 사용

---

### 캘린더 탭

**일정 조회:**
- **오늘 일정** → 오늘 예정된 일정 목록
- **데드라인** → 지정한 일수 내 마감/납품 일정 (기본 14일)

**일정 추가:**
1. 제목, 날짜(YYYY-MM-DD), 시간(HH:MM) 입력
2. **추가 (미리보기)** 클릭으로 먼저 확인

---

### Drive 탭

**파일 검색:**
1. 검색어 입력 (예: `보고서`)
2. **검색** 버튼 클릭
3. 파일 유형별 아이콘으로 구분 (문서/스프레드시트/프레젠테이션/폴더)

**파일 목록:**
1. 유형 선택 (전체/문서/스프레드시트/프레젠테이션/PDF)
2. **목록** 버튼 클릭

---

### Sheets 탭

**스프레드시트 검색:**
1. 검색어 입력 (예: `매출`)
2. 결과 클릭 시 ID가 자동 입력됨

**데이터 읽기:**
1. 스프레드시트 ID 입력 (검색 결과 클릭으로 자동 입력 가능)
2. 범위 입력 (기본: `Sheet1`, 예: `Sheet1!A1:D10`)
3. **읽기** 클릭

---

### 설정 탭

AI 비서 기능을 사용하려면 LLM API 키를 설정해야 합니다.

| Provider | 모델 기본값 | 비용 |
|----------|-----------|------|
| Gemini | gemini-2.5-flash | 무료 tier 있음 |
| Claude | claude-sonnet-4-20250514 | $5 충전 필요 |
| OpenAI | gpt-4o-mini | $5 충전 필요 |

**설정 방법:**
1. Provider 선택
2. API Key 입력
3. 모델 변경 (선택, 비워두면 기본값)
4. **저장** 클릭

> 설정은 `~/.qesg/app_config.json`에 저장되어 다음 실행 시 자동 로드됩니다.

---

## CLI 사용법

터미널에서 직접 명령어로 사용할 수도 있습니다.

### 메일

```bash
qesg mail triage --limit 10          # 읽지 않은 메일 요약
qesg mail list --query "from:홍길동"   # 메일 검색
qesg mail read [메일ID]               # 특정 메일 읽기
qesg mail reply --id [ID] --body "확인했습니다." --dry-run  # 회신 미리보기
qesg mail send --to user@gmail.com --subject "제목" --body "내용"  # 새 메일
qesg mail chat --with 홍길동 --topic 프로젝트  # 대화이력 조회
```

### 캘린더

```bash
qesg schedule agenda                  # 오늘 일정
qesg schedule list --query "회의"      # 일정 검색
qesg schedule add --title "팀 회의" --date 2026-03-15 --time 14:00 --duration 1h
qesg schedule deadlines --days 14     # 데드라인 조회
```

### Google Drive

```bash
qesg doc search "보고서"               # 파일 검색
qesg doc list --type doc              # 파일 목록
qesg doc sync --local ./report.md --drive-path "프로젝트" --dry-run  # 업로드
```

### Google Sheets

```bash
qesg data search --query "매출"                        # 스프레드시트 검색
qesg data read [ID] --range "Sheet1!A1:D10"            # 시트 읽기
qesg data diff --spreadsheet [ID] --sheet1 "시트1" --sheet2 "시트2" --key 종목코드
qesg data append [ID] --range "Sheet1!A1" --values '["데이터1","데이터2"]'
```

### 레시피 (복합 명령)

```bash
qesg recipe morning-triage            # 아침 루틴: 메일 + 일정
qesg recipe mail-context --person 홍길동  # 특정인 대화이력
```

### 기타

```bash
qesg status                           # 시스템 상태 확인
qesg guide                            # AI용 가이드 문서
```

---

## Claude Code 스킬로 등록

AI 에이전트가 직접 조작하게 하려면:

1. 스킬 파일 복사:
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
$env:PATH = "$env:APPDATA\npm;$env:PATH"
gws --version
```

### 데스크톱 앱이 안 열리는 경우
```powershell
# flet 설치 확인
pip show flet

# 직접 실행
python -m qesg.app.main
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
    ├── app/
    │   ├── main.py       # 데스크톱 앱 (Flet UI)
    │   └── llm.py        # LLM 클라이언트
    └── recipes/
        └── __init__.py   # 복합 워크플로우
```
