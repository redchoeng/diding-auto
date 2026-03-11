"""Configuration management — credentials, defaults, state."""
import json
from pathlib import Path

CONFIG_DIR = Path.home() / ".qesg"
CONFIG_FILE = CONFIG_DIR / "config.json"
CREDENTIALS_FILE = CONFIG_DIR / "credentials.json"


def ensure_config_dir():
    CONFIG_DIR.mkdir(exist_ok=True)


def load_config() -> dict:
    ensure_config_dir()
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    return {
        "default_sender": "",
        "gmail_labels": ["INBOX"],
        "drive_root_folder": "",
        "calendar_id": "primary",
        "sheets_default_key": "",
    }


def save_config(cfg: dict):
    ensure_config_dir()
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")


def get_config(key: str, default=None):
    return load_config().get(key, default)
