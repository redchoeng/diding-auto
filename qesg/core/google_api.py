"""Google API 읽기 전용 래퍼 — gws CLI 대체.

모든 함수는 읽기 전용. 쓰기/수정/삭제 API는 의도적으로 구현하지 않음.
"""
from datetime import datetime, timedelta
from qesg.core.google_auth import get_service


# ── Gmail (읽기 전용) ────────────────────────────────────────────────────────

def gmail_triage(limit: int = 10) -> dict:
    """읽지 않은 메일 목록 조회."""
    try:
        svc = get_service("gmail")
        results = svc.users().messages().list(
            userId="me", q="is:unread", maxResults=limit
        ).execute()

        messages = []
        for msg_meta in results.get("messages", []):
            msg = svc.users().messages().get(
                userId="me", id=msg_meta["id"], format="metadata",
                metadataHeaders=["From", "Subject", "Date"]
            ).execute()
            headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
            messages.append({
                "id": msg_meta["id"],
                "from": headers.get("From", ""),
                "subject": headers.get("Subject", "(제목 없음)"),
                "date": headers.get("Date", ""),
                "snippet": msg.get("snippet", ""),
            })
        return {"error": False, "messages": messages}
    except Exception as e:
        return {"error": True, "message": str(e)}


def gmail_read(message_id: str) -> dict:
    """메일 본문 읽기."""
    try:
        svc = get_service("gmail")
        msg = svc.users().messages().get(userId="me", id=message_id, format="full").execute()
        headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}

        body = _extract_body(msg.get("payload", {}))
        return {
            "error": False,
            "id": message_id,
            "from": headers.get("From", ""),
            "subject": headers.get("Subject", ""),
            "date": headers.get("Date", ""),
            "body": body,
        }
    except Exception as e:
        return {"error": True, "message": str(e)}


def gmail_search(query: str, limit: int = 20) -> dict:
    """메일 검색."""
    try:
        svc = get_service("gmail")
        results = svc.users().messages().list(userId="me", q=query, maxResults=limit).execute()

        messages = []
        for msg_meta in results.get("messages", []):
            msg = svc.users().messages().get(
                userId="me", id=msg_meta["id"], format="metadata",
                metadataHeaders=["From", "Subject", "Date"]
            ).execute()
            headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
            messages.append({
                "id": msg_meta["id"],
                "from": headers.get("From", ""),
                "subject": headers.get("Subject", "(제목 없음)"),
                "date": headers.get("Date", ""),
            })
        return {"error": False, "messages": messages}
    except Exception as e:
        return {"error": True, "message": str(e)}


def gmail_chat_history(name: str, limit: int = 20) -> dict:
    """특정인과의 대화이력 조회."""
    try:
        svc = get_service("gmail")
        query = f"from:{name} OR to:{name}"
        results = svc.users().messages().list(userId="me", q=query, maxResults=limit).execute()

        threads = []
        for msg_meta in results.get("messages", []):
            msg = svc.users().messages().get(
                userId="me", id=msg_meta["id"], format="metadata",
                metadataHeaders=["From", "Subject", "Date"]
            ).execute()
            headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
            threads.append({
                "id": msg_meta["id"],
                "from": headers.get("From", ""),
                "subject": headers.get("Subject", ""),
                "date": headers.get("Date", ""),
                "snippet": msg.get("snippet", ""),
            })
        return {"error": False, "threads": threads}
    except Exception as e:
        return {"error": True, "message": str(e)}


def _extract_body(payload: dict) -> str:
    """Extract plain text body from Gmail message payload."""
    import base64

    if payload.get("mimeType") == "text/plain" and payload.get("body", {}).get("data"):
        return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")

    for part in payload.get("parts", []):
        if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
            return base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="replace")
        # Recurse into nested parts
        if part.get("parts"):
            result = _extract_body(part)
            if result:
                return result

    # Fallback: try HTML
    for part in payload.get("parts", []):
        if part.get("mimeType") == "text/html" and part.get("body", {}).get("data"):
            html = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="replace")
            import re
            return re.sub(r"<[^>]+>", "", html)[:3000]

    return ""


# ── Calendar (읽기 전용) ─────────────────────────────────────────────────────

def calendar_agenda(days: int = 1) -> dict:
    """오늘부터 N일간 일정 조회."""
    try:
        svc = get_service("calendar")
        now = datetime.utcnow()
        time_min = now.isoformat() + "Z"
        time_max = (now + timedelta(days=days)).isoformat() + "Z"

        results = svc.events().list(
            calendarId="primary", timeMin=time_min, timeMax=time_max,
            maxResults=50, singleEvents=True, orderBy="startTime"
        ).execute()

        events = []
        for ev in results.get("items", []):
            start = ev.get("start", {}).get("dateTime", ev.get("start", {}).get("date", ""))
            end = ev.get("end", {}).get("dateTime", ev.get("end", {}).get("date", ""))
            events.append({
                "id": ev.get("id", ""),
                "summary": ev.get("summary", "(제목 없음)"),
                "start": start,
                "end": end,
                "location": ev.get("location", ""),
                "description": ev.get("description", "")[:200] if ev.get("description") else "",
            })
        return {"error": False, "events": events}
    except Exception as e:
        return {"error": True, "message": str(e)}


# ── Drive (읽기 전용) ────────────────────────────────────────────────────────

def drive_search(query: str, limit: int = 20) -> dict:
    """Drive 파일 검색."""
    try:
        svc = get_service("drive")
        q = f"name contains '{query}' and trashed=false"
        results = svc.files().list(
            q=q, pageSize=limit,
            fields="files(id, name, mimeType, modifiedTime, webViewLink)",
            orderBy="modifiedTime desc",
        ).execute()
        return {"error": False, "files": results.get("files", [])}
    except Exception as e:
        return {"error": True, "message": str(e)}


def drive_list(file_type: str = "any", limit: int = 20) -> dict:
    """Drive 파일 목록."""
    try:
        svc = get_service("drive")
        mime_map = {
            "doc": "application/vnd.google-apps.document",
            "sheet": "application/vnd.google-apps.spreadsheet",
            "slide": "application/vnd.google-apps.presentation",
            "pdf": "application/pdf",
        }
        q = "trashed=false"
        if file_type != "any" and file_type in mime_map:
            q += f" and mimeType='{mime_map[file_type]}'"

        results = svc.files().list(
            q=q, pageSize=limit,
            fields="files(id, name, mimeType, modifiedTime, webViewLink)",
            orderBy="modifiedTime desc",
        ).execute()
        return {"error": False, "files": results.get("files", [])}
    except Exception as e:
        return {"error": True, "message": str(e)}


def drive_recent(limit: int = 20) -> dict:
    """최근 수정된 파일."""
    return drive_list("any", limit)


# ── Sheets (읽기 전용) ───────────────────────────────────────────────────────

def sheets_read(spreadsheet_id: str, range_name: str = "Sheet1") -> dict:
    """스프레드시트 데이터 읽기."""
    try:
        svc = get_service("sheets")
        result = svc.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id, range=range_name
        ).execute()
        return {"error": False, "data": {"values": result.get("values", [])}}
    except Exception as e:
        return {"error": True, "message": str(e)}


def sheets_search(query: str) -> dict:
    """스프레드시트 검색 (Drive API 활용)."""
    try:
        svc = get_service("drive")
        q = f"name contains '{query}' and mimeType='application/vnd.google-apps.spreadsheet' and trashed=false"
        results = svc.files().list(
            q=q, pageSize=20,
            fields="files(id, name, modifiedTime)",
            orderBy="modifiedTime desc",
        ).execute()
        return {"error": False, "spreadsheets": results.get("files", [])}
    except Exception as e:
        return {"error": True, "message": str(e)}
