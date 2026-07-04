import requests
from . import Settings, Utils
from .Utils import log_debug, log_err
from typing import Dict


def get_lowest_price_info(steamID: int, usd_zar_rate: float = None) -> Dict:
    """
    Return the lowest current gg.deals price in USD and ZAR for a Steam app ID.
    Returns a dictionary with keys 'usd', 'zar', and 'gg_url', or None if no price info is available.
    """

    # Get the exchange rate
    if usd_zar_rate is None:
        try:
            usd_zar_rate = Utils.get_usd_zar_exchange_rate()
        except Exception:
            usd_zar_rate = None

    # Get the info for the given steam ID from either the
    # gg.deals API or the redirect URL, depending on the setting
    if Settings.get_setting('REDIRECT_GGDEALS_API', default='false').lower() == 'true':
        price_info = _request_info_from_redirect(steamID)
    else:
        price_info = request_info_from_gg_deals(steamID)

    if not price_info or 'prices' not in price_info:
        log_err(f"Failed to get price info for Steam ID {steamID}: API returned success=False")
        return None

    # Find the lowest price between the retail and keyshops
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

    # Get the URL for the game on gg.deals
    gg_url = price_info.get('url') if 'url' in price_info else None

    return {
        'usd': lowest_usd,
        'zar': round(lowest_usd * usd_zar_rate, 2) if usd_zar_rate is not None else None,
        'gg_url': gg_url,
    }


def request_info_from_gg_deals(steamID: int) -> Dict:
    """Retrieve gg.deals price information for a Steam app ID."""
    if steamID is None:
        return None

    try:
        apiKey = Settings.get_setting('GGDEALS_API_KEY')
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


def _request_info_from_redirect(steamID: int) -> Dict:
    """Retrieve gg.deals price information for a Steam app ID by redirecting the API call"""
    if steamID is None:
        return None

    print('Redirecting GG deals API')
    url = Settings.get_setting('GGDEALS_REDIRECT_URL')

    try:
        response = requests.get(
            url,
            params={"steam_id": steamID},
        )
    except requests.RequestException as e:
        log_err(f"Error fetching price info for Steam ID {steamID}: {e}")
        return None

    response.raise_for_status()
    payload = response.json()
    return payload
