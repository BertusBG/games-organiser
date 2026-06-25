import requests
import re
import json
import difflib

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

FIXED_GAME_NAME = None  # Set to a specific game name for testing, or None for interactive mode

def get_game_info(game_name: str, exchange_rate=None) -> bool:
    gg_api_key = "pKkjsaEY6SWkPxiyeb0SGHkgSIMfSQVM"

    steam_app_id = find_steam_app_id(game_name)

    if not steam_app_id:
        print("Could not find Steam App ID")
        return True

    request = STEAM_APP_DETAILS_URL.format(steam_app_id)
    steam_response_raw = requests.get(
        request,
        timeout=10
    )
    steam_response = steam_response_raw.json()

    steam_data = steam_response[
        str(steam_app_id)
    ]["data"]

    output_data = {
        "name": steam_data.get("name"),
        "steam_app_id": steam_app_id,
        "thumbnail": steam_data.get("header_image"),
        "release_date": steam_data.get(
            "release_date", {}
        ).get("date"),

        "reviews":
            fetch_review_statistics(
                steam_app_id
            ),

        "steam_price":
            extract_steam_price_information(
                steam_data
            ),

        "gg_lowest_price":
            fetch_gg_deals_price(
                steam_app_id,
                gg_api_key,
                exchange_rate
            ),

        "minimum_requirements":
            extract_minimum_requirements(
                steam_data
            ),

        "store_tags":
            extract_store_tags(
                steam_data
            )
    }

    print(json.dumps(output_data, indent=4))

    return True


# ----------------------------
# STEAM ID RESOLUTION
# ----------------------------
def normalize_title(text):
    return re.sub(r"[^\w\s]", "", (text or "").lower()).strip()


def find_steam_app_id(game_name):
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

        normalized_query = normalize_title(game_name)
        best_match_id = None
        best_score = -1.0

        # Copilot tried something to find the
        # closest match, but it didn't work well.
        # For now, just take the first result.
        for item in [items[0]]:
            title = item.get("name", "")
            normalized_title = normalize_title(title)

            if not normalized_title:
                continue

            if normalized_query == normalized_title:
                return item.get("id")

            if False and (normalized_title.startswith(normalized_query) or normalized_query.startswith(normalized_title)):
                score = 1.0
            else:
                score = difflib.SequenceMatcher(
                    None,
                    normalized_query,
                    normalized_title
                ).ratio()

            if score > best_score:
                best_score = score
                best_match_id = item.get("id")

        return best_match_id

    except:
        return None


def clean_html(text):
    return re.sub(r"<.*?>", "", text or "").strip()


# ----------------------------
# SYSTEM REQUIREMENTS PARSER
# ----------------------------
def parse_system_requirements(requirements_text):
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


def extract_minimum_requirements(steam_data) -> dict:
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
    return parse_system_requirements(
        pc_requirements.get("minimum", "")
    )


def extract_store_tags(steam_data):
    return sorted({
        genre["description"]
        for genre in steam_data.get("genres", [])
    } | {
        category["description"]
        for category in steam_data.get("categories", [])
    })


def fetch_review_statistics(steam_app_id):
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

    except:
        return {
            "percent_positive": 0,
            "total_reviews": 0
        }


def extract_steam_price_information(steam_data):
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


def fetch_usd_to_zar_rate():
    try:
        response = requests.get(
            "https://open.er-api.com/v6/latest/USD",
            timeout=10
        ).json()

        return float(response.get("rates", {}).get("ZAR"))

    except:
        return None


def fetch_gg_deals_price(steam_app_id, gg_api_key, exchange_rate=None):
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

        #for key in ("currentRetail", "currentKeyshops"):
        for key in ("currentKeyshops",): # Don't look at retail prices
            value = price_data.get(key)
            if value is not None:
                candidates.append(float(value))

        # TODO Make sure it's only keys, not
        # accounts or gifts. Will probably involve
        # scraping, if the anti-bot doesn't prevent
        # that.

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

    except:
        return None


if __name__ == "__main__":
    # Clear the console screen
    print("\033c", end="")

    exchange_rate = fetch_usd_to_zar_rate()
    print("USD→ZAR RATE:", exchange_rate)

    if FIXED_GAME_NAME:
        get_game_info(FIXED_GAME_NAME, exchange_rate)
    else:
        while True:
            game_name = input("Enter game name: ")

            if not game_name:
                break

            get_game_info(game_name, exchange_rate)

            print("\n\n")
