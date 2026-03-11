"""Mail commands — triage, reply drafting, conversation context via gws CLI."""
import json as _json
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
    """Unread inbox summary.

    Examples:
        qesg mail triage
        qesg mail triage --limit 5
    """
    result = run_gws(["gmail", "+triage"])
    if result.get("error"):
        error(result["message"], code=result.get("code", "GWS_ERROR"))

    data = result.get("data") or {}
    if isinstance(data, str):
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
@click.option("--query", "search_query", default=None, help="Gmail search query.")
@click.option("--limit", default=20, help="Max results.")
def mail_list(search_query, limit):
    """Search/list emails.

    Examples:
        qesg mail list --query "from:홍길동"
        qesg mail list --query "subject:납품 after:2026/03/01"
    """
    params = {"userId": "me", "maxResults": limit}
    if search_query:
        params["q"] = search_query

    result = run_gws(["gmail", "users", "messages", "list",
                       "--params", _json.dumps(params)])
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
    result = run_gws(["gmail", "users", "messages", "get",
                       "--params", _json.dumps({"userId": "me", "id": message_id})])
    if result.get("error"):
        error(result["message"], code=result.get("code", "GWS_ERROR"))

    emit({"status": "ok", "email": result.get("data")})


@mail.command("reply")
@click.option("--id", "message_id", required=True, help="Message ID to reply to.")
@click.option("--body", required=True, help="Reply body text.")
@click.option("--dry-run", is_flag=True, help="Preview without sending.")
def mail_reply(message_id, body, dry_run):
    """Reply to a message.

    Examples:
        qesg mail reply --id 19cdb4bfdd2a18a4 --body "확인했습니다." --dry-run
    """
    args = ["gmail", "+reply", "--message-id", message_id, "--body", body]
    if dry_run:
        args.append("--dry-run")

    result = run_gws(args)
    if result.get("error"):
        error(result["message"], code=result.get("code", "GWS_ERROR"))

    if dry_run:
        emit({"status": "dry_run", "action": "mail.reply",
              "message_id": message_id, "body": body, "preview": result.get("data")})
    else:
        ok("Reply sent.", data=result.get("data"))


@mail.command("send")
@click.option("--to", required=True, help="Recipient email.")
@click.option("--subject", required=True, help="Subject line.")
@click.option("--body", required=True, help="Email body.")
@click.option("--dry-run", is_flag=True, help="Preview without sending.")
def mail_send(to, subject, body, dry_run):
    """Send a new email.

    Examples:
        qesg mail send --to user@example.com --subject "안녕" --body "내용" --dry-run
    """
    args = ["gmail", "+send", "--to", to, "--subject", subject, "--body", body]
    if dry_run:
        args.append("--dry-run")

    result = run_gws(args)
    if result.get("error"):
        error(result["message"], code=result.get("code", "GWS_ERROR"))

    if dry_run:
        emit({"status": "dry_run", "action": "mail.send",
              "to": to, "subject": subject, "preview": result.get("data")})
    else:
        ok(f"Email sent to {to}.", data=result.get("data"))


@mail.command("chat")
@click.option("--with", "person", required=True, help="Person to look up.")
@click.option("--topic", default=None, help="Filter by topic.")
@click.option("--limit", default=10)
def mail_chat(person, topic, limit):
    """Get conversation history with a person.

    Examples:
        qesg mail chat --with user@example.com --topic 프로젝트
    """
    query = f"from:{person} OR to:{person}"
    if topic:
        query += f" {topic}"

    result = run_gws(["gmail", "users", "messages", "list",
                       "--params", _json.dumps({"userId": "me", "q": query, "maxResults": limit})])
    if result.get("error"):
        error(result["message"], code=result.get("code", "GWS_ERROR"))

    emit({"status": "ok", "person": person, "topic": topic, "data": result.get("data")})
