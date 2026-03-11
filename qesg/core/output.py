"""JSON output formatter — AI agents get structured data, humans get readable text."""
import json
import sys
from datetime import datetime, date


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)


def emit(data: dict, *, compact: bool = False):
    """Print JSON to stdout. All CLI output goes through here."""
    indent = None if compact else 2
    json.dump(data, sys.stdout, cls=JSONEncoder, ensure_ascii=False, indent=indent)
    sys.stdout.write("\n")


def ok(message: str, **extra):
    emit({"status": "ok", "message": message, **extra})


def error(message: str, code: str = "ERROR", **extra):
    emit({"status": "error", "code": code, "message": message, **extra})
    sys.exit(1)


def dry_run_notice(action: str, params: dict):
    emit({
        "status": "dry_run",
        "action": action,
        "params": params,
        "message": "No changes made. Remove --dry-run to execute.",
    })
