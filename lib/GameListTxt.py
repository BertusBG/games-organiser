from pathlib import Path

GAME_NAMES_PATH = Path(__file__).parent.parent / 'data' / 'gameNames.txt'

def get_game_names(ignored_id: None) -> list[str]:
    """Read the names of the games from gameNames.txt and return them as a list."""
    with open(GAME_NAMES_PATH, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]
