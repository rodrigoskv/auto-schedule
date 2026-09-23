"""Atalho para a instância JSON em data/. Equivale a `python main.py --entrada ../data`."""

import sys
from pathlib import Path

from main import main

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


if __name__ == "__main__":
    if "--entrada" not in sys.argv:
        sys.argv[1:1] = ["--entrada", str(DATA_DIR)]
    main()
