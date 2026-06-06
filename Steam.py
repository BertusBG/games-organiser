import requests
from urllib.parse import quote_plus


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

    normalized_query = gameName.strip().lower()
    for item in items:
        name = item.get('name', '').strip().lower()
        if name == normalized_query:
            return item.get('id')

    return items[0].get('id')
