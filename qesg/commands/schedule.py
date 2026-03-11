"""Schedule commands — Google Calendar integration via gws CLI."""
import click
from qesg.core.output import emit, ok, dry_run_notice, error
from qesg.core.gws import run_gws, build_json_arg


@click.group()
def schedule():
    """Calendar — events, agenda, deadline tracking."""
    pass


@schedule.command("agenda")
def schedule_agenda():
    """Show upcoming events across all calendars.

    Examples:
        qesg schedule agenda
    """
    result = run_gws(["calendar", "+agenda"])
    if result.get("error"):
        error(result["message"], code=result.get("code", "GWS_ERROR"))

    emit({"status": "ok", "events": result.get("data")})


@schedule.command("list")
@click.option("--time-min", default=None, help="Start time (RFC3339, e.g. 2026-03-11T00:00:00Z).")
@click.option("--time-max", default=None, help="End time (RFC3339).")
@click.option("--query", "search_query", default=None, help="Free-text search in events.")
@click.option("--limit", default=20, help="Max results.")
def schedule_list(time_min, time_max, search_query, limit):
    """List calendar events with filters.

    Examples:
        qesg schedule list --time-min 2026-03-11T00:00:00Z --time-max 2026-03-18T00:00:00Z
        qesg schedule list --query "납품"
    """
    args = ["calendar", "events", "list", "--calendarId", "primary",
            "--maxResults", str(limit), "--singleEvents", "true", "--orderBy", "startTime"]
    if time_min:
        args += ["--timeMin", time_min]
    if time_max:
        args += ["--timeMax", time_max]
    if search_query:
        args += ["--q", search_query]

    result = run_gws(args)
    if result.get("error"):
        error(result["message"], code=result.get("code", "GWS_ERROR"))

    emit({"status": "ok", "events": result.get("data")})


@schedule.command("add")
@click.option("--title", required=True, help="Event title.")
@click.option("--date", "event_date", required=True, help="Date (YYYY-MM-DD).")
@click.option("--time", "event_time", default=None, help="Time (HH:MM). Omit for all-day.")
@click.option("--duration", default="1h", help="Duration (e.g. 1h, 30m).")
@click.option("--description", default=None, help="Event description.")
@click.option("--dry-run", is_flag=True)
def schedule_add(title, event_date, event_time, duration, description, dry_run):
    """Create a calendar event.

    Examples:
        qesg schedule add --title "3월 납품" --date 2026-03-31 --description "정부 인증 제출"
        qesg schedule add --title "미팅" --date 2026-03-15 --time 14:00 --duration 1h --dry-run
    """
    # Build gws +insert arguments
    args = ["calendar", "+insert", "--summary", title]

    if event_time:
        args += ["--start", f"{event_date}T{event_time}:00"]
        # Calculate end time
        if duration.endswith("h"):
            dur_minutes = int(duration[:-1]) * 60
        elif duration.endswith("m"):
            dur_minutes = int(duration[:-1])
        else:
            dur_minutes = 60
        h, m = event_time.split(":")
        total_min = int(h) * 60 + int(m) + dur_minutes
        end_h, end_m = divmod(total_min, 60)
        args += ["--end", f"{event_date}T{end_h:02d}:{end_m:02d}:00"]
    else:
        args += ["--start", event_date, "--end", event_date]

    if description:
        args += ["--description", description]

    if dry_run:
        dry_run_notice("schedule.add", {
            "title": title, "date": event_date, "time": event_time,
            "duration": duration, "description": description,
        })
        return

    result = run_gws(args)
    if result.get("error"):
        error(result["message"], code=result.get("code", "GWS_ERROR"))

    ok(f"Event created: {title} on {event_date}", event=result.get("data"))


@schedule.command("deadlines")
@click.option("--days", default=30, help="Look-ahead days (default 30).")
@click.option("--keyword", default=None, help="Filter (e.g. 납품, 마감, 제출).")
def schedule_deadlines(days, keyword):
    """Show upcoming deadlines and milestones.

    Examples:
        qesg schedule deadlines --days 14
        qesg schedule deadlines --keyword 납품
    """
    from datetime import datetime, timedelta, timezone
    now = datetime.now(timezone.utc)
    end = now + timedelta(days=days)

    search = keyword or "납품 OR 마감 OR 제출 OR 마일스톤 OR deadline"

    args = ["calendar", "events", "list", "--calendarId", "primary",
            "--timeMin", now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "--timeMax", end.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "--q", search,
            "--singleEvents", "true", "--orderBy", "startTime"]

    result = run_gws(args)
    if result.get("error"):
        error(result["message"], code=result.get("code", "GWS_ERROR"))

    emit({"status": "ok", "days": days, "keyword": keyword,
          "deadlines": result.get("data")})
