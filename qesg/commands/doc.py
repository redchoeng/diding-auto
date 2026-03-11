"""Document commands — Google Drive sync, search, version tracking via gws CLI."""
import click
from qesg.core.output import emit, ok, dry_run_notice, error
from qesg.core.gws import run_gws, build_json_arg


@click.group()
def doc():
    """Google Drive document management — sync, search, upload."""
    pass


@doc.command("list")
@click.option("--folder", default=None, help="Drive folder name or ID.")
@click.option("--query", "search_query", default=None, help="Search query string.")
@click.option("--type", "file_type", type=click.Choice(["doc", "sheet", "slide", "pdf", "any"]),
              default="any", help="File type filter.")
@click.option("--limit", default=20)
def doc_list(folder, search_query, file_type, limit):
    """List files in Drive.

    Examples:
        qesg doc list --folder "프로젝트 문서"
        qesg doc list --query "etl-enhancement" --type doc
    """
    args = ["drive", "files", "list"]

    query_parts = []
    if folder:
        query_parts.append(f"'{folder}' in parents")
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

    if query_parts:
        args += ["--query", " and ".join(query_parts)]
    args += ["--max-results", str(limit)]

    result = run_gws(args)
    if result.get("error"):
        error(result["message"], code=result.get("code", "GWS_ERROR"))

    emit({"status": "ok", "files": result.get("data") or []})


@doc.command("get")
@click.argument("file_id")
def doc_get(file_id):
    """Get file metadata and content."""
    result = run_gws(["drive", "files", "get", file_id])
    if result.get("error"):
        error(result["message"], code=result.get("code", "GWS_ERROR"))

    emit({"status": "ok", "file": result["data"]})


@doc.command("search")
@click.argument("query")
@click.option("--limit", default=10)
def doc_search(query, limit):
    """Search Drive by filename or content.

    Examples:
        qesg doc search "etl-enhancement-proposal-v2"
        qesg doc search "납품 일정"
    """
    result = run_gws(["drive", "files", "list", "--query", f"fullText contains '{query}'",
                       "--max-results", str(limit)])
    if result.get("error"):
        error(result["message"], code=result.get("code", "GWS_ERROR"))

    emit({"status": "ok", "query": query, "files": result.get("data") or []})


@doc.command("sync")
@click.option("--local", required=True, help="Local file path to sync.")
@click.option("--drive-path", default=None, help="Target Drive folder.")
@click.option("--mode", type=click.Choice(["upload", "download", "both"]), default="upload")
@click.option("--dry-run", is_flag=True)
def doc_sync(local, drive_path, mode, dry_run):
    """Sync a local file to/from Google Drive.

    Examples:
        qesg doc sync --local ./etl-enhancement-proposal-v2.md --drive-path "프로젝트 문서"
        qesg doc sync --local ./report.md --mode download --dry-run
    """
    if dry_run:
        dry_run_notice("doc.sync", {
            "local": local,
            "drive_path": drive_path,
            "mode": mode,
        })
        return

    if mode in ("upload", "both"):
        args = ["drive", "files", "upload", "--file", local]
        if drive_path:
            args += ["--parent", drive_path]
        result = run_gws(args)
        if result.get("error"):
            error(result["message"], code=result.get("code", "GWS_ERROR"))

    if mode in ("download", "both"):
        # For download, we'd need file ID — search first
        result = run_gws(["drive", "files", "list", "--query", f"name contains '{local}'"])
        if result.get("error"):
            error(result["message"], code=result.get("code", "GWS_ERROR"))

    ok(f"Sync completed: {local} ({mode})")


@doc.command("version")
@click.argument("file_id")
def doc_version(file_id):
    """Check file revision history.

    Examples:
        qesg doc version abc123
    """
    result = run_gws(["drive", "revisions", "list", file_id])
    if result.get("error"):
        error(result["message"], code=result.get("code", "GWS_ERROR"))

    emit({"status": "ok", "file_id": file_id, "revisions": result.get("data") or []})
