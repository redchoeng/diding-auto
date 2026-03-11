"""Google Workspace CLI (gws) wrapper — all Google API calls go through here.

gws command structure (v0.11):
  gmail:    +triage, +send, +reply, +reply-all, +forward, +watch, users
  calendar: +insert, +agenda, events, calendarList
  drive:    +upload, files, revisions
  sheets:   +read, +append, spreadsheets
"""
import json
import os
import subprocess
import shutil
import sys

# Load .env file if present (for OAuth credentials)
_dotenv_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
if os.path.exists(_dotenv_path):
    with open(_dotenv_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

# Environment setup for gws auth
_ENV = os.environ.copy()

# Resolve gws executable path
_npm_global = os.path.join(os.environ.get("APPDATA", ""), "npm")
_GWS_CMD = os.path.join(_npm_global, "gws.cmd")
if not os.path.exists(_GWS_CMD):
    _GWS_CMD = "gws"  # fallback to PATH lookup

# Ensure PATH includes node (needed by gws.cmd internally)
_extra_paths = [
    r"C:\Program Files\nodejs",
    _npm_global,
]
_ENV["PATH"] = ";".join(_extra_paths) + ";" + _ENV.get("PATH", "")


def check_gws_installed() -> bool:
    try:
        r = subprocess.run(["gws", "--version"], capture_output=True, text=True,
                           timeout=10, env=_ENV)
        return r.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def run_gws(args: list[str], *, timeout: int = 30, fmt: str = "json") -> dict:
    """Execute a gws CLI command and return parsed result."""
    cmd = [_GWS_CMD] + args
    if fmt and "--format" not in args:
        cmd += ["--format", fmt]

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True,
            timeout=timeout, encoding="utf-8", env=_ENV,
        )
    except FileNotFoundError:
        return {"error": True, "code": "GWS_NOT_FOUND",
                "message": "gws CLI not installed. Run: npm install -g @googleworkspace/cli"}
    except subprocess.TimeoutExpired:
        return {"error": True, "code": "TIMEOUT",
                "message": f"gws command timed out after {timeout}s"}

    # Use stdout only for data; stderr has noise like "Using keyring backend: keyring"
    output = result.stdout.strip()
    # Extract JSON portion — find balanced JSON block
    json_str = _extract_json(output)
    if not json_str:
        # Fallback: try combined output
        json_str = _extract_json((result.stdout + "\n" + result.stderr).strip()) or output

    if result.returncode != 0:
        # Try to parse error JSON
        try:
            err = json.loads(json_str)
            return {"error": True, "code": "GWS_ERROR",
                    "message": err.get("error", {}).get("message", str(err)),
                    "raw": err}
        except (json.JSONDecodeError, TypeError):
            return {"error": True, "code": "GWS_ERROR",
                    "message": result.stderr.strip() or json_str or f"exit code {result.returncode}"}

    if not json_str:
        return {"error": False, "data": None}

    try:
        return {"error": False, "data": json.loads(json_str)}
    except json.JSONDecodeError:
        return {"error": False, "data": json_str}


def run_gws_raw(args: list[str], *, timeout: int = 30) -> str:
    try:
        result = subprocess.run(
            [_GWS_CMD] + args, capture_output=True, text=True,
            timeout=timeout, encoding="utf-8", env=_ENV,
        )
        return result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return ""


def build_json_arg(data: dict) -> str:
    """Build JSON string for gws --data argument."""
    return json.dumps(data, ensure_ascii=False)


def _extract_json(text: str) -> str | None:
    """Extract the first complete JSON object/array from text."""
    for start_char, end_char in [("{", "}"), ("[", "]")]:
        idx = text.find(start_char)
        if idx == -1:
            continue
        depth = 0
        in_string = False
        escape = False
        for i in range(idx, len(text)):
            c = text[i]
            if escape:
                escape = False
                continue
            if c == "\\":
                escape = True
                continue
            if c == '"' and not escape:
                in_string = not in_string
                continue
            if in_string:
                continue
            if c == start_char:
                depth += 1
            elif c == end_char:
                depth -= 1
                if depth == 0:
                    return text[idx:i + 1]
    return None
