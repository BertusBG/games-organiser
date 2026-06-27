import json
import sys
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib import Utils, GameInfoCollector

FIXED_GAME_NAME = None  # Set to a specific game name for testing, or None for interactive mode

def print_game_info(game_name: str, exchange_rate=None) -> bool:
    game_info = GameInfoCollector.build_game_info(game_name, exchange_rate)
    if not game_info:
        print("Could not find Steam App ID")
        return True

    print(json.dumps(game_info, indent=4))
    return True


if __name__ == "__main__":
    # Clear the console screen
    print("\033c", end="")

    exchange_rate = Utils.get_usd_zar_exchange_rate()
    print("USD→ZAR RATE:", exchange_rate)

    if FIXED_GAME_NAME:
        print_game_info(FIXED_GAME_NAME, exchange_rate)
    else:
        while True:
            game_name = input("Enter game name: ")

            if not game_name:
                break

            print_game_info(game_name, exchange_rate)

            print("\n\n")
