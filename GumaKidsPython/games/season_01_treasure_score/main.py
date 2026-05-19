from __future__ import annotations

import sys

from engine import check_game_files, run_game


if __name__ == "__main__":
    if "--check" in sys.argv:
        check_game_files()
    else:
        run_game()
