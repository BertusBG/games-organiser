from lib import Steam, GgDeals, Settings
from .Utils import log_debug

def build_game_info(game_name: str, exchange_rate=None):
    steam_app_id = Steam.get_id(game_name)
    if not steam_app_id:
        return None

    steam_response = Steam.get_app_details(steam_app_id)
    steam_data = steam_response.get("data", {})
    if not steam_data:
        return None

    if Settings.get_setting('MOCK_GGDEALS', default='false').lower() == 'true':
        log_debug("MOCK_GGDEALS is enabled, returning mock price info")
        gg_url = "https://supersport.com/"
        lowest_usd = 100
        return {
            'usd': lowest_usd,
            'zar': round(lowest_usd * 16, 2),
            'gg_url': gg_url,
        }
    else:
        gg_lowest_price = GgDeals.get_lowest_price_info(
            steam_app_id,
            exchange_rate,
        )

    return {
        "name": steam_data.get("name"),
        "steam_app_id": steam_app_id,
        "thumbnail": steam_data.get("header_image"),
        "release_date": steam_data.get("release_date", {}).get("date"),
        "reviews": Steam.get_review_statistics(steam_app_id),
        "steam_price": Steam.extract_steam_price_information(steam_data),
        "gg_lowest_price": gg_lowest_price,
        "minimum_requirements": Steam.extract_minimum_requirements(steam_data),
        "store_tags": Steam.extract_store_tags(steam_data),
        "user_tags": Steam.get_user_tags(steam_app_id),
    }

