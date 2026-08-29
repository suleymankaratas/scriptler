"""Nasdaq-100 sayfası."""

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
universe = importlib.import_module("borsa_isleri_src.universe")
fetch = importlib.import_module("borsa_isleri_src.fetch")
favorites = importlib.import_module("borsa_isleri_src.favorites")
analysis = importlib.import_module("borsa_isleri_src.analysis")

render_category_page(
    "Nasdaq-100", universe.get_nasdaq100_symbols(), config, storage, screener, fetch, favorites, analysis,
    name_map=universe.get_nasdaq100_name_map(),
)
