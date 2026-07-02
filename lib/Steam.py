import re
import requests
from urllib.parse import quote_plus
from bs4 import BeautifulSoup

from . import Utils


def get_id(gameName):
    """Return the Steam app ID for a game by searching the Steam store."""
    query = quote_plus(gameName)
    url = f'https://store.steampowered.com/api/storesearch?term={query}&l=en&cc=US&v=1'
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    data = response.json()

    items = data.get('items', [])
    if not items:
        return None

    normalized_query = Utils.normalize_title(gameName)
    for item in items:
        if Utils.normalize_title(item.get('name', '')) == normalized_query:
            return item.get('id')

    return items[0].get('id')


def get_app_details(steam_app_id, language='en', country='ZA'):
    """Return the Steam app details payload for a specific app ID."""
    url = f'https://store.steampowered.com/api/appdetails?appids={steam_app_id}&l={language}&cc={country}'
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.json().get(str(steam_app_id), {})


def get_review_statistics(steam_app_id):
    try:
        review_response = requests.get(
            f'https://store.steampowered.com/appreviews/{steam_app_id}?json=1&language=all',
            timeout=10,
        ).json()

        query_summary = review_response.get('query_summary', {})
        positive_reviews = query_summary.get('total_positive', 0)
        negative_reviews = query_summary.get('total_negative', 0)
        total_reviews = positive_reviews + negative_reviews

        positive_percentage = (
            round((positive_reviews / total_reviews) * 100, 2)
            if total_reviews else 0
        )

        return {
            'percent_positive': positive_percentage,
            'total_reviews': total_reviews,
        }
    except Exception:
        return {
            'percent_positive': 0,
            'total_reviews': 0,
        }


def get_user_tags(steam_app_id):
    try:
        response = requests.get(
            f'https://store.steampowered.com/app/{steam_app_id}',
            timeout=10,
            headers={
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
            },
        )
        response.raise_for_status()
        return _extract_user_tags_from_steam_markup(response.text)
    except Exception:
        return []


def extract_minimum_requirements(steam_data):
    pc_requirements = steam_data.get('pc_requirements', {})
    if not pc_requirements:
        return {
            'operating_system': None,
            'cpu': None,
            'ram': None,
            'gpu': None,
            'storage': None,
            'additional_notes': [],
        }
    return _parse_system_requirements(pc_requirements.get('minimum', ''))


def extract_store_tags(steam_data):
    return sorted({
        genre['description']
        for genre in steam_data.get('genres', [])
    } | {
        category['description']
        for category in steam_data.get('categories', [])
    })


def extract_steam_price_information(steam_data):
    price_overview = steam_data.get('price_overview')

    if not price_overview:
        return {
            'full_price': 'Free',
            'current_price': 'Free',
            'discount_percent': 0,
        }

    # If the game is not on discount, the full price will be blank,
    # so populate that with the current price.
    full_price = price_overview.get('initial_formatted', 'N/A')
    current_price = price_overview.get('final_formatted', 'N/A')

    if not full_price:
        full_price = current_price

    return {
        'full_price': full_price,
        'current_price': current_price,
        'discount_percent': price_overview.get('discount_percent', 0),
    }


def _parse_system_requirements(requirements_text):
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


def _extract_user_tags_from_steam_markup(markup):
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
