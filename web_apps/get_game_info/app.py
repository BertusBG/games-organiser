from flask import Flask, render_template, request, jsonify, Response
import sys
from pathlib import Path

try:
    from ...lib.GameInfoCollector import build_game_info
    from ...lib import GgDeals, Steam
except (ImportError, ValueError):
    # Fall back to a root-based import when running directly.
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from lib.GameInfoCollector import build_game_info
    from lib import GgDeals, Steam

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


def build_batch(game_names):
    results = []

    for name in game_names:
        try:
            info = build_game_info(name)
            if not info:
                results.append({"error": True, "name": name})
                continue

            results.append(format_game_info(info))
        except Exception:
            results.append({"error": True, "name": name})

    return results


@app.route("/", methods=["GET", "POST"])
def index() -> str:
    game_input = ""
    game_infos = []
    error = None

    game_names = []

    # Support URL query param, e.g. /?game=elden+ring
    if request.method == "GET":
        query_game = request.args.get("game", "").strip()

        if query_game:
            game_input = query_game
            game_names = [query_game]

    # Support entering game names in text box using POST
    if request.method == "POST":
        game_input = request.form.get("game_name", "")

        # split into lines (multi-game support)
        game_names = [
            g.strip()
            for g in game_input.splitlines()
            if g.strip()
        ]

    # Shared processing between GET and POST
    if game_names:
        game_infos = build_batch(game_names)
    elif request.method == "POST":
        error = "Please enter at least one game name."

    return render_template(
        "index.html",
        game_input=game_input,
        game_infos=game_infos,
        error=error,
    )

@app.route('/api/ggd', methods=['GET'])
def forward_gg_deals_request() -> Response:
    # Support URL query param, e.g. /ggd?steam_id=220
    steamId = request.args.get("steam_id", "").strip()
    try:
        steamId = int(steamId)
    except:
        return jsonify({"error": "Integer steam_id is required"}), 400

    info = GgDeals.get_price_info(steamId)
    return jsonify(info)

if __name__ == "__main__":
    print("Example: http://127.0.0.1:5000/?game=hades")
    print("\n")
    print("http://127.0.0.1:5000/api/ggd?steam_id=220")
    print("\n")
    app.run(host="0.0.0.0", debug=True, use_reloader=False)
