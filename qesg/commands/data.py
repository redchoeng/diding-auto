"""Data commands — Google Sheets via gws CLI."""
import json as _json
import click
from qesg.core.output import emit, ok, error, dry_run_notice
from qesg.core.gws import run_gws


@click.group()
def data():
    """Google Sheets — read, append, diff."""
    pass


@data.command("read")
@click.argument("spreadsheet_id")
@click.option("--range", "cell_range", default="Sheet1", help="Range (e.g. Sheet1!A1:D10).")
def data_read(spreadsheet_id, cell_range):
    """Read data from a spreadsheet.

    Examples:
        qesg data read abc123 --range "Sheet1!A1:F50"
    """
    result = run_gws(["sheets", "+read", "--spreadsheetId", spreadsheet_id, "--range", cell_range])
    if result.get("error"):
        error(result["message"], code=result.get("code", "GWS_ERROR"))

    emit({"status": "ok", "spreadsheet_id": spreadsheet_id, "range": cell_range,
          "data": result.get("data")})


@data.command("append")
@click.argument("spreadsheet_id")
@click.option("--range", "cell_range", required=True, help="Target range.")
@click.option("--values", required=True, help="JSON array.")
@click.option("--dry-run", is_flag=True)
def data_append(spreadsheet_id, cell_range, values, dry_run):
    """Append a row to a spreadsheet.

    Examples:
        qesg data append abc123 --range "Sheet1!A1" --values '["a","b","c"]'
    """
    try:
        parsed = _json.loads(values)
    except _json.JSONDecodeError:
        error("Invalid JSON for --values.", code="INVALID_JSON")

    if dry_run:
        dry_run_notice("data.append", {
            "spreadsheet_id": spreadsheet_id, "range": cell_range, "values": parsed,
        })
        return

    result = run_gws(["sheets", "+append", "--spreadsheetId", spreadsheet_id,
                       "--range", cell_range, "--values", _json.dumps(parsed, ensure_ascii=False)])
    if result.get("error"):
        error(result["message"], code=result.get("code", "GWS_ERROR"))

    ok(f"Row appended to {cell_range}", data=result.get("data"))


@data.command("diff")
@click.option("--spreadsheet", required=True, help="Spreadsheet ID.")
@click.option("--sheet1", required=True)
@click.option("--sheet2", required=True)
@click.option("--key", required=True, help="Key column name.")
def data_diff(spreadsheet, sheet1, sheet2, key):
    """Compare two sheets by key column.

    Examples:
        qesg data diff --spreadsheet abc123 --sheet1 "시트1" --sheet2 "시트2" --key 종목코드
    """
    r1 = run_gws(["sheets", "+read", "--spreadsheetId", spreadsheet, "--range", sheet1])
    r2 = run_gws(["sheets", "+read", "--spreadsheetId", spreadsheet, "--range", sheet2])

    if r1.get("error"):
        error(f"Failed to read {sheet1}: {r1['message']}", code="SHEET1_ERROR")
    if r2.get("error"):
        error(f"Failed to read {sheet2}: {r2['message']}", code="SHEET2_ERROR")

    rows1 = _parse_sheet(r1.get("data"), key)
    rows2 = _parse_sheet(r2.get("data"), key)

    if rows1 is None or rows2 is None:
        error("Could not parse sheet data.", code="PARSE_ERROR")

    keys1 = set(rows1.keys())
    keys2 = set(rows2.keys())

    only_in_1 = [rows1[k] for k in sorted(keys1 - keys2)]
    only_in_2 = [rows2[k] for k in sorted(keys2 - keys1)]
    changed = []
    for k in sorted(keys1 & keys2):
        if rows1[k] != rows2[k]:
            changed.append({"key": k, "sheet1": rows1[k], "sheet2": rows2[k]})

    emit({
        "status": "ok", "key_column": key,
        "summary": {
            "only_in_sheet1": len(only_in_1), "only_in_sheet2": len(only_in_2),
            "changed": len(changed), "matched": len(keys1 & keys2) - len(changed),
        },
        "only_in_sheet1": only_in_1, "only_in_sheet2": only_in_2, "changed": changed,
    })


@data.command("search")
@click.option("--query", required=True)
@click.option("--limit", default=20)
def data_search(query, limit):
    """Search spreadsheets by name.

    Examples:
        qesg data search --query "매출"
    """
    params = {
        "q": f"mimeType='application/vnd.google-apps.spreadsheet' and name contains '{query}'",
        "pageSize": limit,
    }
    result = run_gws(["drive", "files", "list", "--params", _json.dumps(params)])
    if result.get("error"):
        error(result["message"], code=result.get("code", "GWS_ERROR"))

    emit({"status": "ok", "query": query, "spreadsheets": result.get("data")})


def _parse_sheet(data, key_column: str) -> dict | None:
    if not data:
        return None
    values = None
    if isinstance(data, dict):
        values = data.get("values", [])
    elif isinstance(data, list):
        values = data
    if not values or len(values) < 2:
        return None
    headers = values[0]
    if key_column not in headers:
        return None
    key_idx = headers.index(key_column)
    result = {}
    for row in values[1:]:
        if len(row) > key_idx:
            row_dict = {headers[i]: row[i] if i < len(row) else "" for i in range(len(headers))}
            result[row[key_idx]] = row_dict
    return result
