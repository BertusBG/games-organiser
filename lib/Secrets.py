import json
import os
from pathlib import Path
from typing import Dict


SECRETS_PATH = Path(__file__).parent.parent / 'data' / 'secrets.json'


def load_secrets() -> Dict[str, str]:
    if not SECRETS_PATH.exists():
        print(f'"{SECRETS_PATH}" does not exist')
        return {}

    try:
        print("Loading secrets from JSON")
        return json.loads(SECRETS_PATH.read_text(encoding='utf-8'))
    except json.JSONDecodeError as exc:
        raise ValueError(f'Invalid JSON in {SECRETS_PATH}: {exc}') from exc


def get_secret(name: str) -> str:
    secrets = load_secrets()
    value = secrets.get(name)
    if value is None:
        print("Key not found in JSON, looking for environment variable")
        value = os.environ.get(name)

    if value is None:
        raise KeyError(
            f"Required secret '{name}' not found in {SECRETS_PATH} and no environment variable '{name}' is set."
        )
    return value
