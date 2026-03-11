"""Recipes — pre-defined workflow sequences combining multiple gws commands."""
import click
from qesg.core.output import emit
from qesg.core.gws import run_gws


@click.group()
def recipe():
    """Run pre-defined workflow recipes."""
    pass


@recipe.command("morning-triage")
def morning_triage():
    """Morning routine: unread emails + upcoming agenda + deadlines.

    Combines: gmail +triage + calendar +agenda
    """
    mail_result = run_gws(["gmail", "+triage"])
    cal_result = run_gws(["calendar", "+agenda"])

    emit({
        "status": "ok",
        "recipe": "morning-triage",
        "emails": mail_result.get("data") if not mail_result.get("error") else {"error": mail_result["message"]},
        "agenda": cal_result.get("data") if not cal_result.get("error") else {"error": cal_result["message"]},
    })


@recipe.command("mail-context")
@click.option("--person", required=True, help="Person to look up.")
@click.option("--limit", default=10)
def mail_context(person, limit):
    """Fetch conversation history with a person for context building.

    Examples:
        qesg recipe mail-context --person 김기봉
    """
    result = run_gws(["gmail", "users", "messages", "list", "--userId", "me",
                       "--q", f"from:{person} OR to:{person}",
                       "--maxResults", str(limit)])

    emit({
        "status": "ok",
        "recipe": "mail-context",
        "person": person,
        "data": result.get("data") if not result.get("error") else {"error": result["message"]},
    })
