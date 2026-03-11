"""Mail commands — triage, reply drafting, conversation context via gws CLI."""
import click
from qesg.core.output import emit, ok, dry_run_notice, error
from qesg.core.gws import run_gws


@click.group()
def mail():
    """Mail triage, drafting, and conversation context."""
    pass


@mail.command("triage")
@click.option("--limit", default=20, help="Max results.")
def mail_triage(limit):
    """Unread inbox summary — sender, subject, date.

    Examples:
        qesg mail triage
        qesg mail triage --limit 5
    """
    result = run_gws(["gmail", "+triage"])
    if result.get("error"):
        error(result["message"], code=result.get("code", "GWS_ERROR"))

    data = result.get("data") or {}
    if isinstance(data, str):
        import json as _json
        try:
            data = _json.loads(data)
        except _json.JSONDecodeError:
            emit({"status": "ok", "raw": data})
            return
    messages = data.get("messages", [])[:limit]
    emit({
        "status": "ok",
        "count": len(messages),
        "total_unread": data.get("resultSizeEstimate", 0),
        "emails": messages,
    })


@mail.command("list")
@click.option("--query", "search_query", default=None, help="Gmail search query (e.g. 'from:김기봉 after:2026/03/01').")
@click.option("--limit", default=20, help="Max results.")
def mail_list(search_query, limit):
    """Search/list emails with Gmail query syntax.

    Examples:
        qesg mail list --query "from:김기봉"
        qesg mail list --query "subject:납품 after:2026/03/01"
        qesg mail list --query "is:unread label:INBOX"
    """
    args = ["gmail", "users", "messages", "list", "--userId", "me"]
    if search_query:
        args += ["--q", search_query]
    args += ["--maxResults", str(limit)]

    result = run_gws(args)
    if result.get("error"):
        error(result["message"], code=result.get("code", "GWS_ERROR"))

    emit({"status": "ok", "query": search_query, "data": result.get("data")})


@mail.command("read")
@click.argument("message_id")
def mail_read(message_id):
    """Read a specific email by ID.

    Examples:
        qesg mail read 19cdb4bfdd2a18a4
    """
    result = run_gws(["gmail", "users", "messages", "get", "--userId", "me", "--id", message_id])
    if result.get("error"):
        error(result["message"], code=result.get("code", "GWS_ERROR"))

    emit({"status": "ok", "email": result.get("data")})


@mail.command("reply")
@click.option("--id", "message_id", required=True, help="Message ID to reply to.")
@click.option("--body", required=True, help="Reply body text.")
@click.option("--dry-run", is_flag=True, help="Preview without sending.")
def mail_reply(message_id, body, dry_run):
    """Reply to a message (handles threading automatically).

    Examples:
        qesg mail reply --id 19cdb4bfdd2a18a4 --body "확인했습니다. 감사합니다." --dry-run
    """
    if dry_run:
        dry_run_notice("mail.reply", {"message_id": message_id, "body": body})
        return

    result = run_gws(["gmail", "+reply", "--id", message_id, "--body", body])
    if result.get("error"):
        error(result["message"], code=result.get("code", "GWS_ERROR"))

    ok("Reply sent.", data=result.get("data"))


@mail.command("send")
@click.option("--to", required=True, help="Recipient email.")
@click.option("--subject", required=True, help="Subject line.")
@click.option("--body", required=True, help="Email body.")
@click.option("--dry-run", is_flag=True, help="Preview without sending.")
def mail_send(to, subject, body, dry_run):
    """Send a new email.

    Examples:
        qesg mail send --to user@example.com --subject "회의 안건" --body "내일 회의 안건입니다." --dry-run
    """
    if dry_run:
        dry_run_notice("mail.send", {"to": to, "subject": subject, "body": body})
        return

    result = run_gws(["gmail", "+send", "--to", to, "--subject", subject, "--body", body])
    if result.get("error"):
        error(result["message"], code=result.get("code", "GWS_ERROR"))

    ok(f"Email sent to {to}.", data=result.get("data"))


@mail.command("chat")
@click.option("--with", "person", required=True, help="Person to look up conversation history.")
@click.option("--topic", default=None, help="Filter by topic keyword.")
@click.option("--limit", default=10, help="Max messages.")
def mail_chat(person, topic, limit):
    """Get conversation history with a specific person.

    Examples:
        qesg mail chat --with 김기봉 --topic 제재
        qesg mail chat --with user@example.com --limit 5
    """
    query = f"from:{person} OR to:{person}"
    if topic:
        query += f" {topic}"

    args = ["gmail", "users", "messages", "list", "--userId", "me",
            "--q", query, "--maxResults", str(limit)]

    result = run_gws(args)
    if result.get("error"):
        error(result["message"], code=result.get("code", "GWS_ERROR"))

    emit({
        "status": "ok",
        "person": person,
        "topic": topic,
        "data": result.get("data"),
    })
