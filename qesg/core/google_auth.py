"""Google API 읽기 전용 인증 모듈.

gws CLI를 대체하여 google-api-python-client를 직접 사용.
읽기 전용 스코프만 요청하여 데이터 변경 불가.
"""
import json
import os
import threading
from pathlib import Path

# Read-only scopes only
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
]

_TOKEN_DIR = Path.home() / ".diding"
_TOKEN_PATH = _TOKEN_DIR / "token.json"
_CREDS_PATH = _TOKEN_DIR / "credentials.json"

_services = {}
_lock = threading.Lock()


def _ensure_dir():
    _TOKEN_DIR.mkdir(parents=True, exist_ok=True)


def save_oauth_credentials(client_id: str, client_secret: str):
    """Save OAuth client credentials for later use."""
    _ensure_dir()
    creds_data = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost"],
        }
    }
    with open(_CREDS_PATH, "w", encoding="utf-8") as f:
        json.dump(creds_data, f)


def get_oauth_credentials() -> tuple[str, str]:
    """Load saved OAuth credentials."""
    if not _CREDS_PATH.exists():
        return "", ""
    try:
        with open(_CREDS_PATH, encoding="utf-8") as f:
            data = json.load(f)
        installed = data.get("installed", {})
        return installed.get("client_id", ""), installed.get("client_secret", "")
    except Exception:
        return "", ""


def login(client_id: str = None, client_secret: str = None) -> dict:
    """Perform OAuth login flow. Opens browser for user consent.
    Returns {"success": True, "email": "..."} or {"success": False, "error": "..."}
    """
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError:
        return {"success": False, "error": "google-auth-oauthlib 미설치. pip install google-auth-oauthlib 실행 필요"}

    if client_id and client_secret:
        save_oauth_credentials(client_id, client_secret)

    if not _CREDS_PATH.exists():
        return {"success": False, "error": "OAuth 인증 정보가 없습니다. Client ID와 Secret을 입력하세요."}

    try:
        flow = InstalledAppFlow.from_client_secrets_file(str(_CREDS_PATH), SCOPES)
        creds = flow.run_local_server(port=0, open_browser=True, prompt="consent")

        # Save token
        _ensure_dir()
        with open(_TOKEN_PATH, "w", encoding="utf-8") as f:
            f.write(creds.to_json())

        # Get user email
        email = _get_user_email(creds)
        return {"success": True, "email": email}
    except Exception as e:
        return {"success": False, "error": str(e)}


def logout() -> dict:
    """Revoke token and delete saved credentials."""
    try:
        if _TOKEN_PATH.exists():
            creds = _load_creds()
            if creds and creds.token:
                import requests
                requests.post("https://oauth2.googleapis.com/revoke",
                              params={"token": creds.token})
            _TOKEN_PATH.unlink(missing_ok=True)

        # Clear cached services
        with _lock:
            _services.clear()

        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


def check_auth() -> dict:
    """Check authentication status.
    Returns {"authenticated": True/False, "user": "email@...", "scopes": [...]}
    """
    creds = _load_creds()
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                from google.auth.transport.requests import Request
                creds.refresh(Request())
                with open(_TOKEN_PATH, "w", encoding="utf-8") as f:
                    f.write(creds.to_json())
            except Exception:
                return {"authenticated": False}
        else:
            return {"authenticated": False}

    email = _get_user_email(creds)
    return {
        "authenticated": True,
        "user": email,
        "scopes": SCOPES,
        "readonly": True,
    }


def get_service(api: str, version: str = None):
    """Get an authenticated Google API service.
    Supported: 'gmail', 'calendar', 'drive', 'sheets'
    """
    version_map = {
        "gmail": ("gmail", "v1"),
        "calendar": ("calendar", "v3"),
        "drive": ("drive", "v3"),
        "sheets": ("sheets", "v4"),
    }

    if api not in version_map:
        raise ValueError(f"Unknown API: {api}")

    service_name, default_ver = version_map[api]
    ver = version or default_ver
    cache_key = f"{service_name}_{ver}"

    with _lock:
        if cache_key in _services:
            return _services[cache_key]

    creds = _load_creds()
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            from google.auth.transport.requests import Request
            creds.refresh(Request())
            with open(_TOKEN_PATH, "w", encoding="utf-8") as f:
                f.write(creds.to_json())
        else:
            raise RuntimeError("인증이 필요합니다. 설정에서 Google 로그인을 해주세요.")

    from googleapiclient.discovery import build
    service = build(service_name, ver, credentials=creds, cache_discovery=False)

    with _lock:
        _services[cache_key] = service

    return service


def _load_creds():
    """Load credentials from saved token."""
    if not _TOKEN_PATH.exists():
        return None
    try:
        from google.oauth2.credentials import Credentials
        return Credentials.from_authorized_user_file(str(_TOKEN_PATH), SCOPES)
    except Exception:
        return None


def _get_user_email(creds) -> str:
    """Get user email from credentials."""
    try:
        from googleapiclient.discovery import build
        service = build("oauth2", "v2", credentials=creds, cache_discovery=False)
        info = service.userinfo().get().execute()
        return info.get("email", "")
    except Exception:
        return ""
