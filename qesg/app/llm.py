"""Multi-provider LLM client — Gemini, Claude, OpenAI."""
import json
from qesg.core import google_api

# System prompt that teaches the LLM how to use Google API functions
SYSTEM_PROMPT = """당신은 diding 업무 확인 비서입니다. 사용자의 요청을 처리하기 위해 Google API 도구를 사용합니다.
이 앱은 읽기 전용 모드입니다. 메일 발송, 일정 추가 등 쓰기 작업은 할 수 없습니다.

## 사용 가능한 도구 (읽기 전용)
- `gmail_triage(limit)` — 읽지 않은 메일 요약
- `gmail_read(message_id)` — 메일 본문 읽기
- `gmail_search(query, limit)` — 메일 검색
- `gmail_chat_history(name, limit)` — 특정인과 대화이력 조회
- `calendar_agenda(days)` — N일간 일정 확인
- `drive_search(query, limit)` — Drive 검색
- `drive_list(file_type, limit)` — Drive 파일 목록
- `sheets_read(spreadsheet_id, range_name)` — 시트 읽기

## 규칙
1. 사용자 요청을 분석해서 적절한 도구를 실행하세요.
2. 도구를 실행하려면 [EXEC] 태그를 사용하세요: [EXEC]gmail_triage(5)[/EXEC]
3. 읽기 전용 모드이므로 reply, send, add 등 쓰기 요청은 "읽기 전용 모드입니다"라고 안내하세요.
4. 결과를 한국어로 읽기 쉽게 요약해서 알려주세요.
5. JSON 원문을 그대로 보여주지 말고, 핵심만 정리하세요.

## 메일 초안 참고
사용자가 메일 초안을 요청하면:
1. 먼저 `gmail_chat_history("이름")` 으로 대화이력을 조회하세요.
2. 초안을 작성해서 보여줄 수 있지만, 실제 발송은 불가합니다.
3. "초안을 참고하세요. 실제 발송은 Gmail에서 직접 해주세요." 라고 안내하세요.

## 발신자 그룹핑
메일 요약 시 발신자별로 그룹핑해서 보여주세요:
- 같은 사람에게서 온 메일은 묶어서 표시
- 각 그룹에 대화 맥락 요약 포함
- 긴급도/중요도 순으로 정렬
"""

# Available API functions mapping
_API_FUNCTIONS = {
    "gmail_triage": lambda args: google_api.gmail_triage(**args),
    "gmail_read": lambda args: google_api.gmail_read(**args),
    "gmail_search": lambda args: google_api.gmail_search(**args),
    "gmail_chat_history": lambda args: google_api.gmail_chat_history(**args),
    "calendar_agenda": lambda args: google_api.calendar_agenda(**args),
    "drive_search": lambda args: google_api.drive_search(**args),
    "drive_list": lambda args: google_api.drive_list(**args),
    "drive_recent": lambda args: google_api.drive_recent(**args),
    "sheets_read": lambda args: google_api.sheets_read(**args),
    "sheets_search": lambda args: google_api.sheets_search(**args),
}

# Write commands to block
_WRITE_KEYWORDS = ["reply", "send", "forward", "add", "upload", "append", "delete", "remove", "create"]


def _parse_function_call(expr: str) -> tuple[str, dict]:
    """Parse a function call like 'gmail_triage(5)' or 'gmail_search("query", 10)'.
    Returns (func_name, kwargs_dict)."""
    expr = expr.strip()
    paren_idx = expr.find("(")
    if paren_idx == -1:
        return expr, {}

    func_name = expr[:paren_idx].strip()
    args_str = expr[paren_idx + 1:expr.rfind(")")].strip()

    if not args_str:
        return func_name, {}

    # Try to parse as JSON array for positional args
    try:
        args_list = json.loads(f"[{args_str}]")
    except json.JSONDecodeError:
        # Fallback: treat as single string arg
        args_list = [args_str.strip("\"'")]

    # Map positional args to function parameters
    param_map = {
        "gmail_triage": ["limit"],
        "gmail_read": ["message_id"],
        "gmail_search": ["query", "limit"],
        "gmail_chat_history": ["name", "limit"],
        "calendar_agenda": ["days"],
        "drive_search": ["query", "limit"],
        "drive_list": ["file_type", "limit"],
        "drive_recent": ["limit"],
        "sheets_read": ["spreadsheet_id", "range_name"],
        "sheets_search": ["query"],
    }

    params = param_map.get(func_name, [])
    kwargs = {}
    for i, val in enumerate(args_list):
        if i < len(params):
            kwargs[params[i]] = val

    return func_name, kwargs


def _run_api_call(expr: str) -> str:
    """Execute a Google API function call and return result as string."""
    try:
        func_name, kwargs = _parse_function_call(expr)

        if func_name not in _API_FUNCTIONS:
            return f"Error: Unknown function '{func_name}'"

        result = _API_FUNCTIONS[func_name](kwargs)
        return json.dumps(result, ensure_ascii=False, indent=2)[:3000]
    except Exception as e:
        return f"Error: {e}"


def _is_write_command(cmd: str) -> bool:
    """Check if command is a write operation."""
    cmd_lower = cmd.lower()
    return any(w in cmd_lower for w in _WRITE_KEYWORDS)


def _extract_and_run_commands(text: str) -> tuple[str, list[dict]]:
    """Extract [EXEC]...[/EXEC] commands, run them, return modified text + results.
    Write commands are blocked."""
    results = []
    while "[EXEC]" in text and "[/EXEC]" in text:
        start = text.index("[EXEC]")
        end = text.index("[/EXEC]") + len("[/EXEC]")
        cmd = text[start + 6:end - 7].strip()

        if _is_write_command(cmd):
            text = text[:start] + f"\n⚠️ 읽기 전용 모드: `{cmd}` 실행이 차단되었습니다.\n" + text[end:]
            continue

        output = _run_api_call(cmd)
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
                     {"role": "model", "parts": [{"text": "네, 업무 확인 비서로서 Google API를 활용하겠습니다."}]}]
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
