"""Guide command — AI agents fetch usage docs via this instead of --help."""
import click
from qesg.core.output import emit

GUIDES = {
    "overview": {
        "name": "qesg",
        "version": "0.1.0",
        "description": "AI-agent friendly business workflow CLI wrapping Google Workspace CLI (gws).",
        "commands": ["mail", "doc", "schedule", "data", "guide", "recipe"],
        "design_principles": [
            "All output is JSON for easy AI parsing",
            "--dry-run flag on write operations for safe testing",
            "Minimal output to save tokens",
            "guide command instead of verbose --help",
        ],
        "prerequisites": ["gws CLI installed (npm install -g @anthropic-ai/gws)", "gws auth login completed"],
    },
    "mail": {
        "command": "qesg mail",
        "subcommands": {
            "list": {
                "description": "List/triage emails with grouping",
                "options": ["--date", "--sender", "--label", "--group-by (sender|label|thread)", "--limit"],
                "examples": [
                    "qesg mail list --date 2026-03-11",
                    "qesg mail list --sender 김기봉 --group-by thread",
                ],
            },
            "read": {"description": "Read specific email by ID", "args": ["message_id"]},
            "thread": {"description": "Get full conversation thread", "args": ["thread_id"]},
            "reply": {
                "description": "Draft and send reply with AI context",
                "options": ["--to (required)", "--context (required)", "--thread-id", "--tone", "--dry-run"],
                "examples": [
                    'qesg mail reply --to 김기봉 --context "E16 불가, 사업보고서 대체" --dry-run',
                ],
            },
            "chat": {
                "description": "Get conversation history with a person",
                "options": ["--with (required)", "--topic", "--limit"],
                "examples": ["qesg mail chat --with 김기봉 --topic 제재"],
            },
            "search": {"description": "Free-text email search", "args": ["query"]},
        },
    },
    "doc": {
        "command": "qesg doc",
        "subcommands": {
            "list": {"description": "List Drive files", "options": ["--folder", "--query", "--type", "--limit"]},
            "get": {"description": "Get file metadata", "args": ["file_id"]},
            "search": {"description": "Search Drive", "args": ["query"]},
            "sync": {
                "description": "Sync local file to/from Drive",
                "options": ["--local (required)", "--drive-path", "--mode (upload|download|both)", "--dry-run"],
            },
            "version": {"description": "File revision history", "args": ["file_id"]},
        },
    },
    "schedule": {
        "command": "qesg schedule",
        "subcommands": {
            "list": {
                "description": "List calendar events",
                "options": ["--date", "--range (7d|2w)", "--keyword", "--calendar"],
            },
            "add": {
                "description": "Create calendar event",
                "options": ["--title (required)", "--date (required)", "--time", "--duration", "--description", "--dry-run"],
                "examples": ['qesg schedule add --title "3월 납품" --date 2026-03-31'],
            },
            "deadlines": {
                "description": "Show upcoming deadlines/milestones",
                "options": ["--range", "--keyword"],
            },
        },
    },
    "data": {
        "command": "qesg data",
        "subcommands": {
            "list": {"description": "List spreadsheets", "options": ["--query", "--limit"]},
            "read": {"description": "Read sheet data", "args": ["spreadsheet_id"], "options": ["--sheet", "--range"]},
            "diff": {
                "description": "Compare two sheets by key column",
                "options": ["--sheet1 (required)", "--sheet2 (required)", "--key (required)", "--spreadsheet"],
                "examples": [
                    'qesg data diff --sheet1 "미래에셋 종목" --sheet2 "제재내역" --key 종목코드 --spreadsheet abc123',
                ],
            },
            "write": {
                "description": "Write data to spreadsheet",
                "options": ["--sheet", "--range (required)", "--values (required, JSON)", "--dry-run"],
            },
        },
    },
    "recipe": {
        "command": "qesg recipe",
        "description": "Pre-defined command sequences for common workflows",
        "available_recipes": {
            "morning-triage": "오늘 메일 요약 + 일정 확인 + 납품 데드라인",
            "mail-with-context": "수신인별 대화이력 조회 → 맥락 기반 회신 초안",
            "doc-sync-check": "Drive 문서 최신 버전 확인 + 로컬 싱크",
            "data-cross-check": "두 시트 비교 → 불일치 항목 리포트",
        },
    },
}


@click.command()
@click.argument("topic", default="overview")
def guide(topic):
    """Fetch usage guide for AI agents. Prefer this over --help.

    Examples:
        qesg guide
        qesg guide mail
        qesg guide data
        qesg guide recipe
    """
    topic = topic.lower()
    if topic in GUIDES:
        emit({"status": "ok", "guide": GUIDES[topic]})
    else:
        emit({
            "status": "ok",
            "message": f"No guide for '{topic}'. Available topics:",
            "topics": list(GUIDES.keys()),
        })
