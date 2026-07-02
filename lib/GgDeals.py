import requests
from . import Secrets, Steam, Utils
from .Utils import log_debug, log_err
from typing import Tuple, Dict

# Support mocking out the gg.deals interface, e.g. if the site is blocked
MOCK_OUT = False


def get_lowest_price_info(steamID: int, usd_zar_rate: float = None) -> Dict[str, float]:

    if usd_zar_rate is None:
        try:
            usd_zar_rate = Utils.get_usd_zar_exchange_rate()
        except Exception:
            usd_zar_rate = None

    if MOCK_OUT:
        gg_url = "https://supersport.com/"
        lowest_usd = 100
        return {
            'usd': lowest_usd,
            'zar': round(lowest_usd * usd_zar_rate, 2) if usd_zar_rate is not None else None,
            'gg_url': gg_url,
        }

    """Return the lowest current gg.deals price in USD and ZAR for a Steam app ID."""
    price_info = _get_price_info(steamID)
    if not price_info or 'prices' not in price_info:
        log_err(f"Failed to get price info for Steam ID {steamID}: API returned success=False")
        return None

    prices = price_info.get('prices', {})
    candidates = []
    for field in ('currentRetail', 'currentKeyshops'):
        value = prices.get(field)
        if value is None:
            continue
        try:
            candidates.append(float(value))
        except (ValueError, TypeError):
            continue

    if not candidates:
        log_err(f"No valid price candidates found for Steam ID {steamID}")
        return None

    lowest_usd = min(candidates)

    gg_url = _get_game_page_url(steamID)

    return {
        'usd': lowest_usd,
        'zar': round(lowest_usd * usd_zar_rate, 2) if usd_zar_rate is not None else None,
        'gg_url': gg_url,
    }


def _get_price_info(steamID: int): # -> Dict[str]: # TODO Re-add all return types once module refactored
    """Retrieve gg.deals price information for a Steam app ID."""
    if steamID is None:
        return None

    try:
        apiKey = Secrets.get_secret('GGDEALS_API_KEY')
    except Exception as e:
        log_err('Could not access gg.deals API key')
        log_err(e)
        return None

    url = 'https://api.gg.deals/v1/prices/by-steam-app-id/'
    params = {
        'key': apiKey,
        'ids': str(steamID),
        'region': 'us',
    }

    try:
        payload = Utils.get_with_no_proxy(url, params)
    except requests.RequestException as e:
        log_err(f"Error fetching price info for Steam ID {steamID}: {e}")
        return None

    if not payload.get('success'):
        log_err(f"Failed to get price info for Steam ID {steamID}: API returned success=False")
        log_err(f"gg.deals API error: {payload.get('message', 'Unknown error')}")
        raise ValueError(f"gg.deals API request failed: {payload}")

    data = payload.get('data', {})
    return data.get(str(steamID))


def _get_game_page_url(steamID: int, gameName: str = None) -> str:
    log_debug(f"Looking for gg deals url for steamID {steamID}")
    """Best-effort: return a direct gg.deals game page URL for the given Steam ID or None."""
    info = _get_price_info(steamID)
    if not info:
        log_err(f"No price info found for Steam ID {steamID}, cannot determine gg.deals URL")
        return None

    for key in ('url', 'game_url', 'link'):
        val = info.get(key)
        if isinstance(val, str) and val:
            log_debug(f"Found value '{val}' for key '{key}'")
            return val

    slug = None
    if 'slug' in info and info.get('slug'):
        slug = info.get('slug')
    elif info.get('game') and isinstance(info.get('game'), dict):
        slug = info.get('game').get('slug')

    if slug:
        log_debug(f"Using slug: '{slug}")
        return f"https://gg.deals/game/{slug}/"

    if gameName:
        query = gameName.replace(' ', '+')
        log_debug(f'Replaced spaces in game name -> {query}')
        return f"https://gg.deals/games/?search={query}"

    return None
