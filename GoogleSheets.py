import csv
from urllib.parse import quote
from urllib.request import urlopen

__all__ = [
    'get_column_values',
    'read_public_sheet',
]


def _build_gviz_csv_url(spreadsheet_id: str, sheet_name: str) -> str:
    quoted_sheet_name = quote(sheet_name, safe='')
    return f'https://docs.google.com/spreadsheets/d/{spreadsheet_id}/gviz/tq?tqx=out:csv&sheet={quoted_sheet_name}'


def read_public_sheet(spreadsheet_id: str, sheet_name: str) -> list[dict]:
    """Read a public Google Sheets tab and return rows as dictionaries."""
    url = _build_gviz_csv_url(spreadsheet_id, sheet_name)
    with urlopen(url) as response:
        text = response.read().decode('utf-8').splitlines()

    return list(csv.DictReader(text))


def get_column_values(spreadsheet_id: str, sheet_name: str, column_name: str) -> list[str]:
    """Return all values from a named column in a public Google Sheets tab."""
    rows = read_public_sheet(spreadsheet_id, sheet_name)
    if not rows:
        raise ValueError(f'Sheet "{sheet_name}" is empty or could not be loaded.')
    if column_name not in rows[0]:
        raise ValueError(
            f'Column "{column_name}" not found in sheet "{sheet_name}". '
            f'Available columns: {", ".join(rows[0].keys())}'
        )
    return [row[column_name] for row in rows]
