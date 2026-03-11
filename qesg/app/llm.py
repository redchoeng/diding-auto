"""Multi-provider LLM client — Gemini, Claude, OpenAI."""
import json
import subprocess
import os

# System prompt that teaches the LLM how to use qesg CLI
SYSTEM_PROMPT = """당신은 diding 업무 확인 비서입니다. 사용자의 요청을 처리하기 위해 qesg CLI 도구를 사용합니다.
이 앱은 읽기 전용 모드입니다. 메일 발송, 일정 추가 등 쓰기 작업은 할 수 없습니다.

## 사용 가능한 도구 (읽기 전용)
- `qesg mail triage --limit N` — 읽지 않은 메일 요약
- `qesg mail read <id>` — 메일 본문 읽기
- `qesg mail chat --with "이름" --topic "주제"` — 특정인과 대화이력 조회
- `qesg schedule agenda` — 오늘 일정 확인
- `qesg schedule deadlines --days N` — 마감 데드라인 확인
- `qesg doc search "검색어"` — Drive 검색
- `qesg data read <id> --range "범위"` — 시트 읽기

## 규칙
1. 사용자 요청을 분석해서 적절한 qesg 명령어를 실행하세요.
2. 명령어를 실행하려면 [EXEC] 태그를 사용하세요: [EXEC]qesg mail triage --limit 5[/EXEC]
3. 읽기 전용 모드이므로 reply, send, add 등 쓰기 명령어는 절대 실행하지 마세요.
4. 사용자가 메일 발송이나 일정 추가를 요청하면, "읽기 전용 모드입니다"라고 안내하세요.
5. 결과를 한국어로 읽기 쉽게 요약해서 알려주세요.
6. JSON 원문을 그대로 보여주지 말고, 핵심만 정리하세요.

## 메일 초안 참고
사용자가 메일 초안을 요청하면:
1. 먼저 `qesg mail chat --with "이름"` 으로 대화이력을 조회하세요.
2. 초안을 작성해서 보여줄 수 있지만, 실제 발송은 불가합니다.
3. "초안을 참고하세요. 실제 발송은 Gmail에서 직접 해주세요." 라고 안내하세요.

## 발신자 그룹핑
메일 요약 시 발신자별로 그룹핑해서 보여주세요:
- 같은 사람에게서 온 메일은 묶어서 표시
- 각 그룹에 대화 맥락 요약 포함
- 긴급도/중요도 순으로 정렬
"""

# 쓰기 명령어 차단 목록
_WRITE_COMMANDS = ["mail reply", "mail send", "mail forward", "schedule add", "doc upload", "data append"]


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


def _is_write_command(cmd: str) -> bool:
    """쓰기 명령어인지 확인."""
    cmd_lower = cmd.lower()
    return any(w in cmd_lower for w in _WRITE_COMMANDS)


def _extract_and_run_commands(text: str) -> tuple[str, list[dict]]:
    """Extract [EXEC]...[/EXEC] commands, run them, return modified text + results.
    쓰기 명령어는 차단합니다."""
    results = []
    while "[EXEC]" in text and "[/EXEC]" in text:
        start = text.index("[EXEC]")
        end = text.index("[/EXEC]") + len("[/EXEC]")
        cmd = text[start + 6:end - 7].strip()

        if _is_write_command(cmd):
            text = text[:start] + f"\n⚠️ 읽기 전용 모드: `{cmd}` 실행이 차단되었습니다.\n" + text[end:]
            continue

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
