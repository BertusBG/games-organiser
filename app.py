from flask import Flask, render_template
import csv
from pathlib import Path

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
                })
    return games


@app.route("/")
def index():
    games = load_games()
    return render_template("index.html", games=games)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
