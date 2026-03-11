"""Document commands — Google Drive via gws CLI."""
import json as _json
import click
from qesg.core.output import emit, ok, dry_run_notice, error
from qesg.core.gws import run_gws


@click.group()
def doc():
    """Google Drive — search, list, upload."""
    pass


@doc.command("list")
@click.option("--query", "search_query", default=None, help="Drive search query.")
@click.option("--type", "file_type", type=click.Choice(["doc", "sheet", "slide", "pdf", "any"]),
              default="any")
@click.option("--limit", default=20)
def doc_list(search_query, file_type, limit):
    """List files in Drive.

    Examples:
        qesg doc list --query "보고서" --type doc
    """
    query_parts = []
    if search_query:
        query_parts.append(f"name contains '{search_query}'")
    if file_type != "any":
        mime_map = {
            "doc": "application/vnd.google-apps.document",
            "sheet": "application/vnd.google-apps.spreadsheet",
            "slide": "application/vnd.google-apps.presentation",
            "pdf": "application/pdf",
        }
        query_parts.append(f"mimeType='{mime_map[file_type]}'")

    params = {"pageSize": limit}
    if query_parts:
        params["q"] = " and ".join(query_parts)

    result = run_gws(["drive", "files", "list", "--params", _json.dumps(params)])
    if result.get("error"):
        error(result["message"], code=result.get("code", "GWS_ERROR"))

    emit({"status": "ok", "files": result.get("data")})


@doc.command("search")
@click.argument("query")
@click.option("--limit", default=10)
def doc_search(query, limit):
    """Search Drive by name or content.

    Examples:
        qesg doc search "etl-enhancement"
    """
    params = {"q": f"fullText contains '{query}'", "pageSize": limit}
    result = run_gws(["drive", "files", "list", "--params", _json.dumps(params)])
    if result.get("error"):
        error(result["message"], code=result.get("code", "GWS_ERROR"))

    emit({"status": "ok", "query": query, "files": result.get("data")})


@doc.command("upload")
@click.option("--file", "local_file", required=True, help="Local file path.")
@click.option("--dry-run", is_flag=True)
def doc_upload(local_file, dry_run):
    """Upload a file to Drive.

    Examples:
        qesg doc upload --file ./report.md --dry-run
    """
    args = ["drive", "+upload", "--file", local_file]
    if dry_run:
        args.append("--dry-run")

    result = run_gws(args)
    if result.get("error"):
        error(result["message"], code=result.get("code", "GWS_ERROR"))

    if dry_run:
        emit({"status": "dry_run", "action": "doc.upload",
              "file": local_file, "preview": result.get("data")})
    else:
        ok(f"Uploaded: {local_file}", data=result.get("data"))
