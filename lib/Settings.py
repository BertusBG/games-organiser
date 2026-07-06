import json
import os
from pathlib import Path
from typing import Dict
from .Utils import log_debug, log_err

SETTINGS_PATH = Path(__file__).parent.parent / 'data' / 'settings.json'


def _load_data_from_json(file_path: Path) -> Dict[str, str]:
    if not file_path.exists():
        log_debug(f'"{file_path}" does not exist')
        return {}

    try:
        log_debug("Loading data from JSON")
        return json.loads(file_path.read_text(encoding='utf-8'))
    except json.JSONDecodeError as exc:
        raise ValueError(f'Invalid JSON in {file_path}: {exc}') from exc


def get_setting(name: str, default: str = None) -> str:
    secrets = _load_data_from_json(SETTINGS_PATH)
    value = secrets.get(name)
    if value is None:
        log_debug(f"Key '{name}' not found in JSON, looking for environment variable")
        value = os.environ.get(name)

    if value is None:
        log_debug(f"Key '{name}' not found in JSON or environment variables, returning default value")
        value = default

    log_debug(f"Key '{name}' found, returning value '{value}'")
    return value


def is_true(name:str) -> bool:
    return get_setting(name, default='false').lower() == 'true'
