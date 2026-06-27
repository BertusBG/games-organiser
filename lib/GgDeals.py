import requests
from . import Secrets, Steam, Utils
from .Utils import log_debug, log_err

apiKey = Secrets.get_secret('GGDEALS_API_KEY')


def get_price_info(steamID, region='us'):
    """Retrieve gg.deals price information for a Steam app ID."""
    if steamID is None:
        return None

    url = 'https://api.gg.deals/v1/prices/by-steam-app-id/'
    params = {
        'key': apiKey,
        'ids': str(steamID),
        'region': region,
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


def get_lowest_price_info(steamID, region='us', usd_zar_rate=None):
    """Return the lowest current gg.deals price in USD and ZAR for a Steam app ID."""
    price_info = get_price_info(steamID, region=region)
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


def get_game_info(gameName, region='us', usd_zar_rate=None, fetch_page_url=False):
    """Return Steam ID, lowest price in ZAR, and optional gg.deals game page URL."""
    gameName = Utils.expand_abbreviations(gameName)
    log_debug(f"Fetching info for '{gameName}'")
    steamID = Steam.get_id(gameName)
    log_debug(f"Steam ID: {steamID}")
    if steamID is None:
        log_err(f"Could not find Steam ID for '{gameName}'")
        return None, None, None

    price_zar = get_lowest_price_zar(steamID=steamID, region=region, usd_zar_rate=usd_zar_rate)
    log_debug(f"Lowest price in ZAR: {price_zar}")
    gg_url = None
    if fetch_page_url:
        gg_url = get_game_page_url(steamID, gameName=gameName, region=region)
        log_debug(f"gg.deals URL: {minimise_url(gg_url)}")
    return steamID, price_zar, gg_url


def get_lowest_price_zar(gameName=None, steamID=None, region='us', usd_zar_rate=None):
    """Return the lowest current retail or keyshop price for a game name or Steam ID."""
    if steamID is None:
        steamID = Steam.get_id(gameName)
    if steamID is None:
        log_err(f"Cannot get price: Steam ID not found for '{gameName}'")
        return None

    price_info = get_lowest_price_info(steamID, region=region, usd_zar_rate=usd_zar_rate)
    if not price_info:
        return None
    return price_info.get('zar')


def get_game_page_url(steamID, gameName=None, region='us'):
    log_debug(f"Looking for gg deals url for steamID {steamID}")
    """Best-effort: return a direct gg.deals game page URL for the given Steam ID or None."""
    info = get_price_info(steamID, region=region)
    if not info:
        log_err(f"No price info found for Steam ID {steamID}, cannot determine gg.deals URL")
        return None

    for key in ('url', 'game_url', 'link'):
        val = info.get(key)
        if isinstance(val, str) and val:
            return val

    slug = None
    if 'slug' in info and info.get('slug'):
        slug = info.get('slug')
    elif info.get('game') and isinstance(info.get('game'), dict):
        slug = info.get('game').get('slug')

    if slug:
        return f"https://gg.deals/game/{slug}/"

    if gameName:
        query = gameName.replace(' ', '+')
        return f"https://gg.deals/games/?search={query}"

    return None


def minimise_url(gg_url: str) -> str:
    from urllib.parse import urlparse

    if not gg_url:
        return 'N/A'

    s = gg_url.strip()
    parsed = urlparse(s)
    path = parsed.path or s
    segments = [seg for seg in path.split('/') if seg]
    if segments:
        return segments[-1]
    return 'N/A'
