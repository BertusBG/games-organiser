import requests
import Steam
import Utils
import Secrets

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

    response = requests.get(url, params=params, headers=headers, timeout=10)
    response.raise_for_status()
    payload = response.json()

    if not payload.get('success'):
        raise ValueError(f"gg.deals API request failed: {payload}")

    data = payload.get('data', {})
    return data.get(str(steamID))


def get_lowest_price_zar(gameName, region='us', usd_zar_rate=None):
    """Return the lowest current retail or keyshop price for a game name."""
    steamID = Steam.get_id(gameName)
    if steamID is None:
        return None

    price_info = get_price_info(steamID, region=region)
    if not price_info or 'prices' not in price_info:
        return None

    prices = price_info['prices']
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
        return None

    rate = usd_zar_rate if usd_zar_rate is not None else Utils.get_usd_zar_exchange_rate()
    return min(candidates) * rate


def get_game_page_url(steamID, gameName=None, region='us'):
    """Best-effort: return a direct gg.deals game page URL for the given Steam ID or None."""
    info = get_price_info(steamID, region=region)
    if not info:
        return None

    # Try common fields that may contain slug or url
    # API structures can vary; check multiple possibilities
    # 1) direct url
    for key in ('url', 'game_url', 'link'):
        val = info.get(key)
        if isinstance(val, str) and val:
            return val

    # 2) slug under top-level or nested 'game'
    slug = None
    if 'slug' in info and info.get('slug'):
        slug = info.get('slug')
    elif info.get('game') and isinstance(info.get('game'), dict):
        slug = info.get('game').get('slug')

    if slug:
        return f"https://gg.deals/game/{slug}/"

    # 3) fallback: try constructing a search URL using the provided name
    if gameName:
        query = gameName.replace(' ', '+')
        return f"https://gg.deals/games/?search={query}"

    return None
