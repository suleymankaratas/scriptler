"""BIST100 dışı diğer BIST hisseleri sayfası."""

import importlib
import sys
from pathlib import Path

WORKSPACE_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = WORKSPACE_DIR.parent

sys.path.insert(0, str(WORKSPACE_DIR))
from project_loader import load_project_package  # noqa: E402
from borsa_category_view import render_category_page  # noqa: E402

load_project_package("borsa_isleri_src", ROOT_DIR / "borsa-isleri" / "src")
config = importlib.import_module("borsa_isleri_src.config")
storage = importlib.import_module("borsa_isleri_src.storage")
screener = importlib.import_module("borsa_isleri_src.screener")
fetch = importlib.import_module("borsa_isleri_src.fetch")
favorites = importlib.import_module("borsa_isleri_src.favorites")
analysis = importlib.import_module("borsa_isleri_src.analysis")

render_category_page(
    "Diğer Hisseler (BIST100 Dışı)", config.TICKERS["diger_bist"], config, storage, screener, fetch, favorites, analysis
)
