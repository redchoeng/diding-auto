"""Schedule commands — Google Calendar integration via gws CLI."""
import json as _json
import click
from datetime import datetime, timedelta, timezone
from qesg.core.output import emit, ok, dry_run_notice, error
from qesg.core.gws import run_gws


@click.group()
def schedule():
    """Calendar — events, agenda, deadline tracking."""
    pass


@schedule.command("agenda")
def schedule_agenda():
    """Show upcoming events.

    Examples:
        qesg schedule agenda
    """
    result = run_gws(["calendar", "+agenda"])
    if result.get("error"):
        error(result["message"], code=result.get("code", "GWS_ERROR"))

    emit({"status": "ok", "events": result.get("data")})


@schedule.command("list")
@click.option("--time-min", default=None, help="Start (RFC3339).")
@click.option("--time-max", default=None, help="End (RFC3339).")
@click.option("--query", "search_query", default=None, help="Search keyword.")
@click.option("--limit", default=20)
def schedule_list(time_min, time_max, search_query, limit):
    """List calendar events with filters.

    Examples:
        qesg schedule list --query "납품"
        qesg schedule list --time-min 2026-03-11T00:00:00Z --time-max 2026-03-18T00:00:00Z
    """
    params = {"singleEvents": True, "orderBy": "startTime", "maxResults": limit}
    if time_min:
        params["timeMin"] = time_min
    if time_max:
        params["timeMax"] = time_max
    if search_query:
        params["q"] = search_query

    result = run_gws(["calendar", "events", "list",
                       "--params", _json.dumps(params)])
    if result.get("error"):
        error(result["message"], code=result.get("code", "GWS_ERROR"))

    emit({"status": "ok", "events": result.get("data")})


@schedule.command("add")
@click.option("--title", required=True, help="Event title.")
@click.option("--date", "event_date", required=True, help="Date (YYYY-MM-DD).")
@click.option("--time", "event_time", default=None, help="Time (HH:MM).")
@click.option("--duration", default="1h", help="Duration (e.g. 1h, 30m).")
@click.option("--description", default=None)
@click.option("--dry-run", is_flag=True)
def schedule_add(title, event_date, event_time, duration, description, dry_run):
    """Create a calendar event.

    Examples:
        qesg schedule add --title "3월 납품" --date 2026-03-31
        qesg schedule add --title "미팅" --date 2026-03-15 --time 14:00 --duration 1h --dry-run
    """
    if duration.endswith("h"):
        dur_minutes = int(duration[:-1]) * 60
    elif duration.endswith("m"):
        dur_minutes = int(duration[:-1])
    else:
        dur_minutes = 60

    if event_time:
        start = f"{event_date}T{event_time}:00+09:00"
        h, m = event_time.split(":")
        total_min = int(h) * 60 + int(m) + dur_minutes
        end_h, end_m = divmod(total_min, 60)
        end = f"{event_date}T{end_h:02d}:{end_m:02d}:00+09:00"
    else:
        start = event_date
        end = event_date

    args = ["calendar", "+insert", "--summary", title, "--start", start, "--end", end]
    if description:
        args += ["--description", description]
    if dry_run:
        args.append("--dry-run")

    result = run_gws(args)
    if result.get("error"):
        error(result["message"], code=result.get("code", "GWS_ERROR"))

    if dry_run:
        emit({"status": "dry_run", "action": "schedule.add",
              "title": title, "start": start, "end": end, "preview": result.get("data")})
    else:
        ok(f"Event created: {title} on {event_date}", event=result.get("data"))


@schedule.command("deadlines")
@click.option("--days", default=30, help="Look-ahead days.")
@click.option("--keyword", default=None, help="Filter keyword.")
def schedule_deadlines(days, keyword):
    """Show upcoming deadlines.

    Examples:
        qesg schedule deadlines --days 14
        qesg schedule deadlines --keyword 납품
    """
    now = datetime.now(timezone.utc)
    end = now + timedelta(days=days)

    search = keyword or "납품 OR 마감 OR 제출 OR 마일스톤 OR deadline"

    params = {
        "timeMin": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "timeMax": end.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "q": search,
        "singleEvents": True,
        "orderBy": "startTime",
    }

    result = run_gws(["calendar", "events", "list",
                       "--params", _json.dumps(params)])
    if result.get("error"):
        error(result["message"], code=result.get("code", "GWS_ERROR"))

    emit({"status": "ok", "days": days, "keyword": keyword, "deadlines": result.get("data")})
