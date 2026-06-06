import requests


def get_usd_zar_exchange_rate():
    """Return the current USD to ZAR exchange rate."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    # Try a public endpoint that does not require an API key.
    try:
        response = requests.get(
            'https://open.er-api.com/v6/latest/USD',
            headers=headers,
            timeout=10,
        )
        response.raise_for_status()
        payload = response.json()
        rate = payload.get('rates', {}).get('ZAR')
        if rate is not None:
            return float(rate)
    except Exception:
        pass

    # Fallback to another free endpoint.
    try:
        response = requests.get(
            'https://api.frankfurter.app/latest',
            params={'from': 'USD', 'to': 'ZAR'},
            headers=headers,
            timeout=10,
        )
        response.raise_for_status()
        payload = response.json()
        rate = payload.get('rates', {}).get('ZAR')
        if rate is not None:
            return float(rate)
    except Exception:
        pass

    raise ValueError('USD to ZAR exchange rate not available')


def print_in_columns(names):
    col_width = 26
    lines = []

    for i in range(0, len(names), 3):
        row_names = names[i:i + 3]
        row_cells = [name[:col_width].ljust(col_width) for name in row_names]
        while len(row_cells) < 3:
            row_cells.append(' ' * col_width)
        lines.append('  '.join(row_cells))

    print('\n'.join(lines))
