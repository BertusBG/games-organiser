import re
import requests
from enum import Enum, auto
from bs4 import BeautifulSoup


class LogLevel(Enum):
    NONE = auto()
    DEBUG = auto()
    ERROR = auto()


LOG_LEVEL = LogLevel.ERROR


def log_debug(message):
    if LOG_LEVEL == LogLevel.DEBUG:
        print(f"<<< {message} >>>")


def log_err(message):
    if LOG_LEVEL in (LogLevel.DEBUG, LogLevel.ERROR):
        print(f"!!! ERROR: {message} !!!")


def get_usd_zar_exchange_rate():
    """Return the current USD to ZAR exchange rate."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

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


def parse_system_requirements(requirements_text):
    requirements_text = requirements_text or ""
    requirements_text = re.sub(r"<br\s*/?>", "\n", requirements_text)
    requirements_text = re.sub(r"<.*?>", "", requirements_text)

    requirement_lines = [
        line.strip()
        for line in requirements_text.split("\n")
        if line.strip()
    ]

    structured_requirements = {
        "operating_system": None,
        "cpu": None,
        "ram": None,
        "gpu": None,
        "storage": None,
        "additional_notes": []
    }

    gpu_label_pattern = re.compile(r"(Graphics|GPU|Video(?:\s*Card)?):\s*(.+)", re.I)

    for requirement_line in requirement_lines:
        lower_line = requirement_line.lower()
        gpu_match = gpu_label_pattern.search(requirement_line)
        if gpu_match:
            structured_requirements["gpu"] = gpu_match.group(2).strip()
            continue

        if "os" in lower_line:
            structured_requirements["operating_system"] = requirement_line.split(":", 1)[-1].strip()
        elif "processor" in lower_line or "cpu" in lower_line:
            structured_requirements["cpu"] = requirement_line.split(":", 1)[-1].strip()
        elif "memory" in lower_line or "ram" in lower_line:
            structured_requirements["ram"] = requirement_line.split(":", 1)[-1].strip()
        elif "storage" in lower_line or "disk" in lower_line:
            structured_requirements["storage"] = requirement_line.split(":", 1)[-1].strip()
        else:
            structured_requirements["additional_notes"].append(requirement_line)

    return structured_requirements


def extract_user_tags_from_steam_markup(markup):
    if not markup:
        return []

    soup = BeautifulSoup(markup, "html.parser")
    tags = []

    for anchor in soup.select(".glance_tags a.app_tag"):
        tag_name = anchor.get_text(" ", strip=True)
        if tag_name:
            tags.append(tag_name)

    if not tags:
        for anchor in soup.select("a.app_tag"):
            tag_name = anchor.get_text(" ", strip=True)
            if tag_name:
                tags.append(tag_name)

    return tags
