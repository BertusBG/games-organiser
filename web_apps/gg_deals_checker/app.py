from flask import Flask, Response, render_template, stream_with_context
import csv
import traceback
import os
import sys
from pathlib import Path

# Add parent directories to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from lib import GameListTxt
from lib import GgDeals
from lib import Secrets
from lib import Utils
from lib.Utils import log_debug, log_err

MAX_GAMES = 10  # limit for testing

app = Flask(__name__)

CSV_PATH = Path(__file__).parent.parent.parent / "data" / "names_and_prices.csv"


def load_games():
    games = []
    try:
        if CSV_PATH.exists():
            log_debug(f"Loading games from {CSV_PATH}")
            with CSV_PATH.open(newline="", encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile)
                for index,row in enumerate(reader):
                    if MAX_GAMES and index >= MAX_GAMES:
                        break  # limit to first MAX_GAMES for testing
                    games.append({
                        "Name": row.get("Name", ""),
                        "SteamID": row.get("SteamID", ""),
                        "LowestPriceZAR": row.get("LowestPriceZAR", ""),
                        "GGDealsURL": row.get("GGDealsURL", ""),
                    })
            log_debug(f"Successfully loaded {len(games)} games")
        else:
            log_err(f"CSV file not found at {CSV_PATH}")
    except Exception as e:
        log_err(f"Error loading games: {e}")
        log_err(traceback.format_exc())
    return games


@app.route("/")
def index():
    try:
        log_debug("Loading index page")
        games = load_games()
        log_debug(f"Rendering index with {len(games)} games")
        return render_template("index.html", games=games)
    except Exception as e:
        log_err(f"Error rendering index: {e}")
        log_err(traceback.format_exc())
        return "Error loading page", 500


def regenerate_csv(names, filename=None, region="us"):
    if filename is None:
        filename = str(Path(__file__).parent.parent.parent / "data" / "names_and_prices.csv")
    usd_zar_rate = Utils.get_usd_zar_exchange_rate()
    fieldnames = ["Name", "SteamID", "LowestPriceZAR", "GGDealsURL"]

    with open(filename, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        csvfile.flush()
        os.fsync(csvfile.fileno())
        yield "Starting regeneration...\n"

        for index, name in enumerate(names):

            if MAX_GAMES and index >= MAX_GAMES:
                break  # limit to first MAX_GAMES for testing

            steam_id = None
            price_zar = None
            gg_url = None
            try:
                log_debug(f"Getting game info for '{name}' from gg.deals")
                steam_id, price_zar, gg_url = GgDeals.get_game_info(
                    name, usd_zar_rate=usd_zar_rate
                )
                log_debug(f"Steam id for {name}: {steam_id}")
                if price_zar:
                    log_debug(f"Price: R {price_zar:.2f}")
                log_debug(f"url: {gg_url}")
            except Exception as e:
                log_err(f"Error getting info for '{name}': {e}")
                log_err(traceback.format_exc())
                price_zar = None

            writer.writerow(
                {
                    "Name": name,
                    "SteamID": steam_id or "",
                    "LowestPriceZAR": f"{price_zar:.2f}" if price_zar is not None else "",
                    "GGDealsURL": gg_url or "",
                }
            )
            # ensure each row is flushed to disk so partial runs persist
            csvfile.flush()
            os.fsync(csvfile.fileno())

            yield f'Processed "{name}": SteamID={steam_id}, LowestPriceZAR={price_zar}\n'

    yield "Regeneration complete.\n"


@app.route("/regenerate", methods=["POST"])
def regenerate():
    def generate():
        try:
            log_debug("Regeneration request started")
            sheet_id = Secrets.get_secret("SPREADSHEET_ID")
            log_debug(f"Retrieved spreadsheet ID")
            names = GameListTxt.get_game_names(sheet_id)
            log_debug(f"{len(names)} games read from sheet")
            # inform the client how many items will be processed so a progress bar can be shown
            total_to_process = len(names) if not MAX_GAMES else min(len(names), MAX_GAMES)
            log_debug(f"Processing {total_to_process} games (MAX_GAMES={MAX_GAMES})")
            yield f"TOTAL:{total_to_process}\n"
            yield from regenerate_csv(names)
            log_debug("Regeneration completed successfully")
        except Exception as exc:
            log_err(f"Error during regeneration: {exc}")
            log_err(traceback.format_exc())
            yield f"Error: {exc}\n"

    return Response(stream_with_context(generate()), mimetype="text/plain")


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
