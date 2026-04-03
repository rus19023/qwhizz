# runapp.py

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "common"))
sys.path.insert(0, str(ROOT / "apps"))

from qwhizz import main

main()