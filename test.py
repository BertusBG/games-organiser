import csv
import os

import GoogleSheets
import GameListTxt
import GgDeals
import Secrets
import Utils

HBAR = '-' * 80

def write_names_and_prices_to_csv(names, filename='names_and_prices.csv', region='us'):
    """Write each game name and its lowest ZAR price to a CSV file."""
    usd_zar_rate = Utils.get_usd_zar_exchange_rate()
    fieldnames = ['Name', 'SteamID', 'LowestPriceZAR']
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for name in names:
            steam_id = None
            price_zar = None
            try:
                steam_id, price_zar, _ = GgDeals.get_game_info(
                    name, region=region, usd_zar_rate=usd_zar_rate
                )
            except Exception:
                print(f"Error getting info for '{name}'")
                price_zar = None

            print(f'Processed "{name}": SteamID={steam_id}, LowestPriceZAR={price_zar}')
            writer.writerow({
                'Name': name,
                'SteamID': steam_id or '',
                'LowestPriceZAR': f'{price_zar:.2f}' if price_zar is not None else '',
            })

    return filename


def print_lowest_prices_for_names(names: list[str], region='us', max_num_games=None):
    """Print the lowest ZAR price for each name, with W40k rewritten."""
    usd_zar_rate = Utils.get_usd_zar_exchange_rate()

    for index, name in enumerate(names):
        steam_id = None
        price_zar = None
        gg_url = None
        try:
            steam_id, price_zar, gg_url = GgDeals.get_game_info(
                name, region=region, usd_zar_rate=usd_zar_rate, fetch_page_url=True
            )
        except Exception:
            print(f"Error getting info for '{name}'")
            price_zar = None

        gg_url = GgDeals.minimise_url(gg_url)

        if price_zar is not None:
            price_str = f'R {price_zar:.2f}'
        else:
            price_str = 'N/A'

        # Truncate or pad name to 20 chars, steam_id to 10 chars for neat printing
        nameCap = 30
        name = name[:nameCap].ljust(nameCap)
        steam_id = str(steam_id).ljust(8)

        print(f'{name} {steam_id} {price_str:>10}   {gg_url}')

        if max_num_games is not None and index+1 >= max_num_games:
            break

    print(f"\nProcessed {index + 1} games.")

if __name__ == '__main__':
    os.system('cls' if os.name == 'nt' else 'clear')
    SPREADSHEET_ID = Secrets.get_secret('SPREADSHEET_ID')
    sheet_name = 'Database '
    column_name = 'Name'
    names = GameListTxt.get_game_names(SPREADSHEET_ID)

    print_lowest_prices_for_names(names, max_num_games=1)
