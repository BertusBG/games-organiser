import re
import requests
from enum import Enum, auto


class LogLevel(Enum):
    NONE = auto()
    DEBUG = auto()
    ERROR = auto()


LOG_LEVEL = LogLevel.DEBUG


def log_debug(message):
    if LOG_LEVEL == LogLevel.DEBUG:
        print(f"<<< {message} >>>")


def log_err(message):
    if LOG_LEVEL in (LogLevel.DEBUG, LogLevel.ERROR):
        print(f"!!! ERROR: {message} !!!")

def get_with_no_proxy(url, params = None):
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    session = requests.Session()
    session.trust_env = False
    if params:
        response = session.get(
            url,
            params=params,
            headers=headers,
            timeout=10,
            proxies={"http": None, "https": None},
        )
    else:
        response = requests.get(
            'https://open.er-api.com/v6/latest/USD',
            headers=headers,
            timeout=10,
            proxies={"http": None, "https": None},
        )
    response.raise_for_status()
    return response.json()

def get_usd_zar_exchange_rate():
    """Return the current USD to ZAR exchange rate."""

    try:
        log_debug("Fetching USD to ZAR exchange rate from open.er-api.com")
        payload = get_with_no_proxy('https://open.er-api.com/v6/latest/USD')
        rate = payload.get('rates', {}).get('ZAR')
        if rate is not None:
            return float(rate)
    except Exception:
        pass

    try:
        log_debug("Fetching USD to ZAR exchange rate from frankfurter.app")
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

    return None


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


def expand_abbreviations(name):
    """Expand common abbreviations in game names."""
    name = name.replace('W40k', 'Warhammer 40,000')
    return name


def normalize_title(text):
    return re.sub(r"[^\w\s]", "", (text or "").lower()).strip()


def clean_html(text):
    return re.sub(r"<.*?>", "", text or "").strip()


def minimise_url(url: str) -> str:
    from urllib.parse import urlparse

    if not url:
        return 'N/A'

    s = url.strip()
    parsed = urlparse(s)
    path = parsed.path or s
    segments = [seg for seg in path.split('/') if seg]
    if segments:
        return segments[-1]
    return 'N/A'
