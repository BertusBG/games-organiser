import json
from pathlib import Path


SECRETS_PATH = Path(__file__).parent.parent / 'data' / 'secrets.json'


def load_secrets() -> dict[str, str]:
    try:
        return json.loads(SECRETS_PATH.read_text(encoding='utf-8'))
    except FileNotFoundError as exc:
        raise FileNotFoundError(
            f'Secrets file not found: {SECRETS_PATH}.\n'
            'Copy secrets.example.json to secrets.json and fill in your values.'
        ) from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f'Invalid JSON in {SECRETS_PATH}: {exc}') from exc


def get_secret(name: str) -> str:
    secrets = load_secrets()
    value = secrets.get(name)
    if value is None:
        raise KeyError(
            f"Required secret '{name}' not found in {SECRETS_PATH}."
        )
    return value
