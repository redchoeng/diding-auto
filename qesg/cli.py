"""qesg — AI-agent friendly business workflow CLI.

Wraps Google Workspace CLI (gws) to provide:
- Mail triage & reply drafting
- Google Drive document sync
- Calendar schedule & deadline tracking
- Google Sheets data analysis & diff

All output is JSON. Designed for AI agent consumption.
"""
import click
from qesg import __version__
from qesg.commands.mail import mail
from qesg.commands.doc import doc
from qesg.commands.schedule import schedule
from qesg.commands.data import data
from qesg.commands.guide import guide
from qesg.recipes import recipe
from qesg.core.output import emit
from qesg.core.gws import check_gws_installed


@click.group()
@click.version_option(__version__, prog_name="qesg")
def main():
    """qesg — AI-agent friendly business workflow CLI.

    Wraps Google Workspace CLI (gws) for mail, docs, calendar, and sheets.
    All output is JSON. Use 'qesg guide' for AI-readable documentation.
    """
    pass


# Register command groups
main.add_command(mail)
main.add_command(doc)
main.add_command(schedule)
main.add_command(data)
main.add_command(guide)
main.add_command(recipe)


@main.command("status")
def status():
    """Check system status — gws installation, auth, connectivity."""
    from qesg.core.gws import run_gws_raw, run_gws, _GWS_CMD
    import os

    gws_exists = os.path.exists(_GWS_CMD)
    checks = {
        "gws_installed": gws_exists,
        "gws_path": _GWS_CMD if gws_exists else None,
        "version": __version__,
    }

    if gws_exists:
        ver = run_gws_raw(["--version"])
        checks["gws_version"] = ver or "unknown"
        # Check auth
        auth = run_gws(["auth", "status"])
        if not auth.get("error"):
            data = auth.get("data", {})
            checks["authenticated"] = True
            checks["user"] = data.get("user", "unknown") if isinstance(data, dict) else "unknown"
        else:
            checks["authenticated"] = False
    else:
        checks["gws_version"] = None
        checks["setup_instructions"] = [
            "1. Install Node.js: https://nodejs.org",
            "2. Install gws: npm install -g @googleworkspace/cli",
            "3. Setup auth: gws auth setup",
            "4. Login: gws auth login",
        ]

    emit({"status": "ok", "checks": checks})


if __name__ == "__main__":
    main()
