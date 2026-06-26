import csv
from urllib.parse import quote
from urllib.request import urlopen

from . import Utils
from .Utils import log_debug, log_err

__all__ = [
    'get_column_values',
    'read_public_sheet',
]

def get_game_names(sheet_id: str) -> list[str]:
    """Fetch game names from a public Google Sheets tab."""
    return get_column_values(sheet_id, "Database ", "Name")


def _build_gviz_csv_url(spreadsheet_id: str, sheet_name: str) -> str:
    quoted_sheet_name = quote(sheet_name, safe='')
    return f'https://docs.google.com/spreadsheets/d/{spreadsheet_id}/gviz/tq?tqx=out:csv&sheet={quoted_sheet_name}'


def read_public_sheet(spreadsheet_id: str, sheet_name: str) -> list[dict]:
    """Read a public Google Sheets tab and return rows as dictionaries."""
    url = _build_gviz_csv_url(spreadsheet_id, sheet_name)
    try:
        with urlopen(url) as response:
            text = response.read().decode('utf-8').splitlines()
    except Exception as e:
        log_err(f"Error fetching public sheet {spreadsheet_id} / {sheet_name}: {e}")
        raise

    return list(csv.DictReader(text))


def get_column_values(spreadsheet_id: str, sheet_name: str, column_name: str) -> list[str]:
    """Return all values from a named column in a public Google Sheets tab."""
    rows = read_public_sheet(spreadsheet_id, sheet_name)
    if not rows:
        log_err(f'Sheet "{sheet_name}" is empty or could not be loaded for spreadsheet {spreadsheet_id}.')
        raise ValueError(f'Sheet "{sheet_name}" is empty or could not be loaded.')
    if column_name not in rows[0]:
        log_err(
            f'Column "{column_name}" not found in sheet "{sheet_name}" for spreadsheet {spreadsheet_id}. '
            f'Available columns: {", ".join(rows[0].keys())}'
        )
        raise ValueError(
            f'Column "{column_name}" not found in sheet "{sheet_name}". '
            f'Available columns: {", ".join(rows[0].keys())}'
        )
    return [row[column_name] for row in rows]
