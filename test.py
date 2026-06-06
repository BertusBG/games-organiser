import csv

import GoogleSheets
import GgDeals
import Secrets
import Steam
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
            name = name.replace('W40k', 'Warhammer 40,000')
            steam_id = None
            price_zar = None
            try:
                steam_id = Steam.get_id(name)
                if steam_id is not None:
                    price_zar = GgDeals.get_lowest_price_zar(name, region=region, usd_zar_rate=usd_zar_rate)
            except Exception:
                price_zar = None

            print(f'Processed "{name}": SteamID={steam_id}, LowestPriceZAR={price_zar}')
            writer.writerow({
                'Name': name,
                'SteamID': steam_id or '',
                'LowestPriceZAR': f'{price_zar:.2f}' if price_zar is not None else '',
            })

    return filename


def print_lowest_prices_for_names(names, region='us'):
    """Print the lowest ZAR price for each name, with W40k rewritten."""
    usd_zar_rate = Utils.get_usd_zar_exchange_rate()

    for name in names:
        if not 'W40k' in name:
            continue

        search_name = name.replace('W40k', 'Warhammer 40,000')
        steam_id = None
        price_zar = None
        try:
            steam_id = Steam.get_id(search_name)
            if steam_id is not None:
                price_zar = GgDeals.get_lowest_price_zar(search_name, region=region, usd_zar_rate=usd_zar_rate)
        except Exception:
            price_zar = None

        if price_zar is not None:
            print(f'{name}: SteamID={steam_id}, LowestPriceZAR=R {price_zar:.2f}')
        else:
            print(f'{name}: SteamID={steam_id or "N/A"}, LowestPriceZAR=not available')



if __name__ == '__main__':
    SPREADSHEET_ID = Secrets.get_secret('SPREADSHEET_ID')
    sheet_name = 'Database '
    column_name = 'Name'
    names = GoogleSheets.get_column_values(SPREADSHEET_ID, sheet_name, column_name)

    write_names_and_prices_to_csv(names)
    #print_lowest_prices_for_names(names)
