"""Multi-provider LLM client — Gemini, Claude, OpenAI."""
import json
import subprocess
import os

# System prompt that teaches the LLM how to use qesg CLI
SYSTEM_PROMPT = """당신은 업무 자동화 비서입니다. 사용자의 요청을 처리하기 위해 qesg CLI 도구를 사용합니다.

## 사용 가능한 도구 (qesg CLI)
- `qesg mail triage --limit N` — 읽지 않은 메일 요약
- `qesg mail read <id>` — 메일 본문 읽기
- `qesg mail reply --id <id> --body "내용"` — 메일 회신
- `qesg mail send --to email --subject "제목" --body "내용"` — 새 메일
- `qesg mail chat --with "이름" --topic "주제"` — 특정인과 대화이력 조회
- `qesg schedule agenda` — 오늘 일정
- `qesg schedule add --title "제목" --date YYYY-MM-DD --time HH:MM` — 일정 추가
- `qesg schedule deadlines --days N` — 마감 데드라인
- `qesg doc search "검색어"` — Drive 검색
- `qesg data read <id> --range "범위"` — 시트 읽기

## 규칙
1. 사용자 요청을 분석해서 적절한 qesg 명령어를 실행하세요.
2. 명령어를 실행하려면 [EXEC] 태그를 사용하세요: [EXEC]qesg mail triage --limit 5[/EXEC]
3. 쓰기 작업(reply, send, add)은 먼저 사용자에게 확인을 받으세요.
4. 결과를 한국어로 읽기 쉽게 요약해서 알려주세요.
5. JSON 원문을 그대로 보여주지 말고, 핵심만 정리하세요.

## 메일 초안 작성 워크플로우
사용자가 메일 회신이나 초안 작성을 요청하면:
1. 먼저 `qesg mail chat --with "이름"` 으로 해당 인물과 주고받은 대화이력을 조회하세요.
2. 대화 맥락을 파악한 후, 적절한 톤과 내용으로 초안을 작성하세요.
3. 초안을 사용자에게 보여주고, 수정사항 확인 후 발송하세요.
4. 초안 작성 시 이전 대화의 맥락, 상대방의 어조, 진행 중인 안건을 반영하세요.

## 일정 추출 워크플로우
메일이나 대화에서 날짜/시간/마감 정보가 발견되면:
1. "이 메일에 일정 정보가 있습니다" 라고 알려주세요.
2. 날짜, 시간, 제목을 추출하여 캘린더 추가를 제안하세요.
3. 사용자가 동의하면 `qesg schedule add` 명령어로 등록하세요.
예: "3월 31일 납품" → `qesg schedule add --title "납품" --date 2026-03-31`

## 발신자 그룹핑
메일 요약 시 발신자별로 그룹핑해서 보여주세요:
- 같은 사람에게서 온 메일은 묶어서 표시
- 각 그룹에 대화 맥락 요약 포함
- 긴급도/중요도 순으로 정렬
"""


def _run_qesg(cmd: str) -> str:
    """Execute a qesg CLI command and return output."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            timeout=30, encoding="utf-8",
            env={**os.environ,
                 "PATH": os.path.join(os.environ.get("APPDATA", ""), "npm") + ";" +
                         r"C:\Program Files\nodejs;" + os.environ.get("PATH", "")},
        )
        return result.stdout.strip() or result.stderr.strip()
    except Exception as e:
        return f"Error: {e}"


def _extract_and_run_commands(text: str) -> tuple[str, list[dict]]:
    """Extract [EXEC]...[/EXEC] commands, run them, return modified text + results."""
    results = []
    while "[EXEC]" in text and "[/EXEC]" in text:
        start = text.index("[EXEC]")
        end = text.index("[/EXEC]") + len("[/EXEC]")
        cmd = text[start + 6:end - 7].strip()
        output = _run_qesg(cmd)
        results.append({"command": cmd, "output": output})
        text = text[:start] + f"\n```\n{cmd}\n→ 실행 완료\n```\n" + text[end:]
    return text, results


class LLMClient:
    """Unified LLM client supporting multiple providers."""

    def __init__(self):
        self.provider = None  # "gemini", "claude", "openai"
        self.api_key = None
        self.model = None
        self.history = []

    def configure(self, provider: str, api_key: str, model: str = None):
        self.provider = provider
        self.api_key = api_key
        self.model = model or self._default_model()
        self.history = []

    def _default_model(self) -> str:
        defaults = {
            "gemini": "gemini-2.5-flash",
            "claude": "claude-sonnet-4-20250514",
            "openai": "gpt-4o-mini",
        }
        return defaults.get(self.provider, "")

    def is_configured(self) -> bool:
        return bool(self.provider and self.api_key)

    def chat(self, user_message: str) -> str:
        """Send message, get response, auto-execute any [EXEC] commands."""
        if not self.is_configured():
            return "LLM이 설정되지 않았습니다. 설정 탭에서 API 키를 입력하세요."

        self.history.append({"role": "user", "content": user_message})

        try:
            if self.provider == "gemini":
                response = self._call_gemini(user_message)
            elif self.provider == "claude":
                response = self._call_claude(user_message)
            elif self.provider == "openai":
                response = self._call_openai(user_message)
            else:
                response = "지원하지 않는 LLM 프로바이더입니다."
        except Exception as e:
            response = f"LLM 호출 오류: {e}"

        # Execute any [EXEC] commands in the response
        response, exec_results = _extract_and_run_commands(response)

        # If commands were executed, send results back to LLM for summary
        if exec_results:
            context = "\n\n".join(
                f"명령어: {r['command']}\n결과:\n{r['output'][:2000]}"
                for r in exec_results
            )
            follow_up = f"다음 명령어 실행 결과를 사용자에게 한국어로 읽기 쉽게 요약해주세요:\n\n{context}"
            self.history.append({"role": "assistant", "content": response})
            self.history.append({"role": "user", "content": follow_up})

            try:
                if self.provider == "gemini":
                    response = self._call_gemini(follow_up)
                elif self.provider == "claude":
                    response = self._call_claude(follow_up)
                elif self.provider == "openai":
                    response = self._call_openai(follow_up)
            except Exception as e:
                # Fallback: show raw results
                response = "\n\n".join(
                    f"**{r['command']}**\n{r['output'][:500]}"
                    for r in exec_results
                )

        self.history.append({"role": "assistant", "content": response})

        # Keep history manageable
        if len(self.history) > 20:
            self.history = self.history[-20:]

        return response

    def _call_gemini(self, message: str) -> str:
        from google import genai
        client = genai.Client(api_key=self.api_key)

        contents = [{"role": "user", "parts": [{"text": SYSTEM_PROMPT}]},
                     {"role": "model", "parts": [{"text": "네, 업무 자동화 비서로서 qesg CLI를 활용하겠습니다."}]}]
        for msg in self.history:
            role = "user" if msg["role"] == "user" else "model"
            contents.append({"role": role, "parts": [{"text": msg["content"]}]})

        response = client.models.generate_content(
            model=self.model,
            contents=contents,
        )
        return response.text

    def _call_claude(self, message: str) -> str:
        import anthropic
        client = anthropic.Anthropic(api_key=self.api_key)

        messages = []
        for msg in self.history:
            messages.append({"role": msg["role"], "content": msg["content"]})

        response = client.messages.create(
            model=self.model,
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            messages=messages,
        )
        return response.content[0].text

    def _call_openai(self, message: str) -> str:
        from openai import OpenAI
        client = OpenAI(api_key=self.api_key)

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for msg in self.history:
            messages.append({"role": msg["role"], "content": msg["content"]})

        response = client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=2048,
        )
        return response.choices[0].message.content
