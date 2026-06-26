from flask import Flask, render_template, request
import sys
from pathlib import Path

try:
    from ...lib.GameInfoCollector import build_game_info
except (ImportError, ValueError):
    # Fall back to a root-based import when running directly.
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from lib.GameInfoCollector import build_game_info

app = Flask(__name__, template_folder="templates")


def format_game_info(game_info):
    if not game_info:
        return None

    return {
        "name": game_info.get("name"),
        "steam_app_id": game_info.get("steam_app_id"),
        "thumbnail": game_info.get("thumbnail"),
        "release_date": game_info.get("release_date"),
        "reviews": game_info.get("reviews"),
        "steam_price": game_info.get("steam_price"),
        "gg_lowest_price": game_info.get("gg_lowest_price"),
        "minimum_requirements": game_info.get("minimum_requirements"),
        "store_tags": game_info.get("store_tags"),
        "user_tags": game_info.get("user_tags"),
    }


@app.route("/", methods=["GET", "POST"])
def index():
    game_name = None
    game_info = None
    error = None

    if request.method == "POST":
        game_name = request.form.get("game_name", "").strip()
        if not game_name:
            error = "Please enter a game name."
        else:
            try:
                game_info = build_game_info(game_name)
                if not game_info:
                    error = "Could not find Steam App ID or game info for the requested title."
                else:
                    game_info = format_game_info(game_info)
            except Exception as exc:
                error = str(exc)

    return render_template(
        "index.html",
        game_name=game_name,
        game_info=game_info,
        error=error,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
