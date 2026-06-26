import requests
import re
import json
import difflib
from pathlib import Path
from bs4 import BeautifulSoup

from lib.Secrets import get_secret

def build_game_info(game_name: str, exchange_rate=None):
    gg_api_key = get_secret('GGDEALS_API_KEY')

    steam_app_id = _find_steam_app_id(game_name)
    if not steam_app_id:
        return None

    request_url = STEAM_APP_DETAILS_URL.format(steam_app_id)
    steam_response_raw = requests.get(
        request_url,
        timeout=10
    )
    steam_response = steam_response_raw.json()

    steam_data = steam_response[
        str(steam_app_id)
    ]["data"]

    return {
        "name": steam_data.get("name"),
        "steam_app_id": steam_app_id,
        "thumbnail": steam_data.get("header_image"),
        "release_date": steam_data.get(
            "release_date", {}
        ).get("date"),
        "reviews": _fetch_review_statistics(steam_app_id),
        "steam_price": _extract_steam_price_information(steam_data),
        "gg_lowest_price": _fetch_gg_deals_price(
            steam_app_id,
            gg_api_key,
            exchange_rate
        ),
        "minimum_requirements": _extract_minimum_requirements(steam_data),
        "store_tags": _extract_store_tags(steam_data),
        "user_tags": _fetch_user_tags(steam_app_id)
    }

def fetch_usd_to_zar_rate():
    try:
        response = requests.get(
            "https://open.er-api.com/v6/latest/USD",
            timeout=10
        ).json()

        return float(response.get("rates", {}).get("ZAR"))
    except Exception:
        return None

STEAM_SEARCH_URL = (
    "https://store.steampowered.com/api/storesearch/"
    "?term={}&l=en&cc=US"
)

STEAM_APP_DETAILS_URL = (
    "https://store.steampowered.com/api/appdetails"
    "?appids={}&l=en"
)

STEAM_REVIEWS_URL_TEMPLATE = (
    "https://store.steampowered.com/appreviews/"
    "{}?json=1&language=all"
)


def _normalize_title(text):
    return re.sub(r"[^\w\s]", "", (text or "").lower()).strip()


def _find_steam_app_id(game_name):
    try:
        response = requests.get(
            STEAM_SEARCH_URL.format(
                requests.utils.quote(game_name)
            ),
            timeout=10
        ).json()

        items = response.get("items", [])
        if not items:
            return None

        normalized_query = _normalize_title(game_name)
        best_match_id = None
        best_score = -1.0

        for item in [items[0]]:
            title = item.get("name", "")
            normalized_title = _normalize_title(title)

            if not normalized_title:
                continue

            if normalized_query == normalized_title:
                return item.get("id")

            score = difflib.SequenceMatcher(
                None,
                normalized_query,
                normalized_title
            ).ratio()

            if score > best_score:
                best_score = score
                best_match_id = item.get("id")

        return best_match_id

    except Exception:
        return None


def _clean_html(text):
    return re.sub(r"<.*?>", "", text or "").strip()


def _parse_system_requirements(requirements_text):
    requirements_text = requirements_text or ""

    requirements_text = re.sub(
        r"<br\s*/?>", "\n", requirements_text
    )
    requirements_text = re.sub(
        r"<.*?>", "", requirements_text
    )

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

    gpu_label_pattern = re.compile(
        r"(Graphics|GPU|Video(?:\s*Card)?):\s*(.+)",
        re.I
    )

    for requirement_line in requirement_lines:
        lower_line = requirement_line.lower()

        gpu_match = gpu_label_pattern.search(requirement_line)
        if gpu_match:
            structured_requirements["gpu"] = (
                gpu_match.group(2).strip()
            )
            continue

        if "os" in lower_line:
            structured_requirements["operating_system"] = (
                requirement_line.split(":", 1)[-1].strip()
            )
        elif "processor" in lower_line or "cpu" in lower_line:
            structured_requirements["cpu"] = (
                requirement_line.split(":", 1)[-1].strip()
            )
        elif "memory" in lower_line or "ram" in lower_line:
            structured_requirements["ram"] = (
                requirement_line.split(":", 1)[-1].strip()
            )
        elif "storage" in lower_line or "disk" in lower_line:
            structured_requirements["storage"] = (
                requirement_line.split(":", 1)[-1].strip()
            )
        else:
            structured_requirements["additional_notes"].append(
                requirement_line
            )

    return structured_requirements


def _extract_minimum_requirements(steam_data) -> dict:
    pc_requirements = steam_data.get("pc_requirements", {})
    if not pc_requirements:
        return {
            "operating_system": None,
            "cpu": None,
            "ram": None,
            "gpu": None,
            "storage": None,
            "additional_notes": []
        }
    return _parse_system_requirements(
        pc_requirements.get("minimum", "")
    )


def _extract_store_tags(steam_data):
    return sorted({
        genre["description"]
        for genre in steam_data.get("genres", [])
    } | {
        category["description"]
        for category in steam_data.get("categories", [])
    })


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


def _fetch_user_tags(steam_app_id):
    try:
        response = requests.get(
            f"https://store.steampowered.com/app/{steam_app_id}",
            timeout=10,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (X11; Linux x86_64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                )
            }
        )
        response.raise_for_status()
        return _extract_user_tags_from_steam_markup(response.text)
    except Exception:
        return []


def _fetch_review_statistics(steam_app_id):
    try:
        review_response = requests.get(
            STEAM_REVIEWS_URL_TEMPLATE.format(steam_app_id),
            timeout=10
        ).json()

        query_summary = review_response.get("query_summary", {})
        positive_reviews = query_summary.get("total_positive", 0)
        negative_reviews = query_summary.get("total_negative", 0)
        total_reviews = positive_reviews + negative_reviews

        positive_percentage = (
            round((positive_reviews / total_reviews) * 100, 2)
            if total_reviews else 0
        )

        return {
            "percent_positive": positive_percentage,
            "total_reviews": total_reviews
        }
    except Exception:
        return {
            "percent_positive": 0,
            "total_reviews": 0
        }


def _extract_steam_price_information(steam_data):
    price_overview = steam_data.get("price_overview")

    if not price_overview:
        return {
            "full_price": "Free",
            "current_price": "Free",
            "discount_percent": 0
        }

    return {
        "full_price": price_overview.get(
            "initial_formatted", "N/A"
        ),
        "current_price": price_overview.get(
            "final_formatted", "N/A"
        ),
        "discount_percent": price_overview.get(
            "discount_percent", 0
        )
    }


def _fetch_gg_deals_price(steam_app_id, gg_api_key, exchange_rate=None):
    if not gg_api_key:
        return None

    gg_url = (
        "https://api.gg.deals/v1/"
        "prices/by-steam-app-id/"
    )

    params = {
        "key": gg_api_key,
        "ids": str(steam_app_id),
        "region": "us"
    }

    try:
        response = requests.get(
            gg_url,
            params=params,
            timeout=10
        ).json()

        if not response.get("success"):
            return None

        game_data = response.get(
            "data", {}
        ).get(str(steam_app_id), {})

        price_data = game_data.get("prices", {})
        candidates = []

        for key in ("currentKeyshops",):
            value = price_data.get(key)
            if value is not None:
                candidates.append(float(value))

        if not candidates:
            return None

        lowest_usd = min(candidates)
        exchange_rate = exchange_rate or fetch_usd_to_zar_rate()

        return {
            "usd": lowest_usd,
            "zar": (
                round(lowest_usd * exchange_rate, 2)
                if exchange_rate else None
            ),
            "exchange_rate": exchange_rate
        }
    except Exception:
        return None

