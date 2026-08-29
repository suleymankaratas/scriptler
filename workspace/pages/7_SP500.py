"""S&P 500 sayfası."""

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

render_category_page(
    "S&P 500", universe.get_snp500_symbols(), config, storage, screener, fetch,
    name_map=universe.get_snp500_name_map(),
)
