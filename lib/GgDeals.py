import requests
from . import Secrets, Steam, Utils
from .Utils import log_debug, log_err

apiKey = Secrets.get_secret('GGDEALS_API_KEY')


def get_game_info(gameName: str, usd_zar_rate: float = None) -> tuple[int, float, str]:
    """Return Steam ID, lowest price in ZAR, and optional gg.deals game page URL."""
    gameName = Utils.expand_abbreviations(gameName)
    log_debug(f"Fetching info for '{gameName}'")
    steamID = Steam.get_id(gameName)
    log_debug(f"Steam ID: {steamID}")
    if steamID is None:
        log_err(f"Could not find Steam ID for '{gameName}'")
        return None, None, None

    price_info = get_lowest_price_info(steamID, usd_zar_rate)
    price_zar = price_info.get('zar')
    log_debug(f"Lowest price in ZAR: {price_zar}")

    gg_url = _get_game_page_url(steamID, gameName=gameName)
    log_debug(f"gg.deals URL: {Utils.minimise_url(gg_url)}")
    return steamID, price_zar, gg_url


def get_lowest_price_info(steamID: int, usd_zar_rate: float = None) -> dict[str, float]:
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
    if usd_zar_rate is None:
        try:
            usd_zar_rate = Utils.get_usd_zar_exchange_rate()
        except Exception:
            usd_zar_rate = None

    return {
        'usd': lowest_usd,
        'zar': round(lowest_usd * usd_zar_rate, 2) if usd_zar_rate is not None else None,
    }


def _get_price_info(steamID: int) -> dict[str]:
    """Retrieve gg.deals price information for a Steam app ID."""
    if steamID is None:
        return None

    url = 'https://api.gg.deals/v1/prices/by-steam-app-id/'
    params = {
        'key': apiKey,
        'ids': str(steamID),
        'region': 'us',
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        session = requests.Session()
        session.trust_env = False
        response = session.get(
            url,
            params=params,
            headers=headers,
            timeout=10,
            proxies={"http": None, "https": None},
        )
        response.raise_for_status()
        payload = response.json()
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
