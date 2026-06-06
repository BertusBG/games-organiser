from flask import Flask, Response, render_template, stream_with_context
import csv
from pathlib import Path

import GoogleSheets
import GgDeals
import Secrets
import Steam
import Utils

app = Flask(__name__)

CSV_PATH = Path(__file__).parent / "names_and_prices.csv"


def load_games():
    games = []
    if CSV_PATH.exists():
        with CSV_PATH.open(newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                games.append({
                    "Name": row.get("Name", ""),
                    "SteamID": row.get("SteamID", ""),
                    "LowestPriceZAR": row.get("LowestPriceZAR", ""),
                    "GGDealsURL": row.get("GGDealsURL", ""),
                })
    return games


@app.route("/")
def index():
    games = load_games()
    return render_template("index.html", games=games)


def generate_csv_regeneration(names, filename="names_and_prices.csv", region="us"):
    usd_zar_rate = Utils.get_usd_zar_exchange_rate()
    fieldnames = ["Name", "SteamID", "LowestPriceZAR", "GGDealsURL"]

    with open(filename, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        yield "Starting regeneration...\n"

        for name in names:
            name = name.replace("W40k", "Warhammer 40,000")
            steam_id = None
            price_zar = None
            gg_url = None
            try:
                steam_id = Steam.get_id(name)
                if steam_id is not None:
                    price_zar = GgDeals.get_lowest_price_zar(
                        name, region=region, usd_zar_rate=usd_zar_rate
                    )
                    # best-effort: fetch a direct gg.deals game page URL
                    try:
                        gg_url = GgDeals.get_game_page_url(steam_id, gameName=name, region=region)
                    except Exception:
                        gg_url = None
            except Exception:
                price_zar = None

            writer.writerow(
                {
                    "Name": name,
                    "SteamID": steam_id or "",
                    "LowestPriceZAR": f"{price_zar:.2f}" if price_zar is not None else "",
                    "GGDealsURL": gg_url or "",
                }
            )

            yield f'Processed "{name}": SteamID={steam_id}, LowestPriceZAR={price_zar}\n'

    yield "Regeneration complete.\n"


@app.route("/regenerate", methods=["POST"])
def regenerate():
    def generate():
        try:
            sheet_id = Secrets.get_secret("SPREADSHEET_ID")
            names = GoogleSheets.get_column_values(sheet_id, "Database ", "Name")
            # inform the client how many items will be processed so a progress bar can be shown
            yield f"TOTAL:{len(names)}\n"
            yield from generate_csv_regeneration(names)
        except Exception as exc:
            yield f"Error: {exc}\n"

    return Response(stream_with_context(generate()), mimetype="text/plain")


if __name__ == "__main__":
    app.run(debug=True)
