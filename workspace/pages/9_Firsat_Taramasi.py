"""Fırsat Taraması — tüm kategorileri (BIST100, Diğer Hisseler, Emtia,
Nasdaq-100, S&P 500, Kripto) birlikte tarar; uzun süredir ucuz/yatay kalmış
adayları öne çıkarır.

Not: Bu YATIRIM TAVSİYESİ değildir — sadece dikkat çekici adayları filtreler,
karar ve inceleme kullanıcıya aittir.
"""

import importlib
import sys
from pathlib import Path

import streamlit as st

WORKSPACE_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = WORKSPACE_DIR.parent

sys.path.insert(0, str(WORKSPACE_DIR))
from project_loader import load_project_package  # noqa: E402
from borsa_category_view import add_name_column, render_last_update_banner, rename_for_display  # noqa: E402

load_project_package("borsa_isleri_src", ROOT_DIR / "borsa-isleri" / "src")
config = importlib.import_module("borsa_isleri_src.config")
storage = importlib.import_module("borsa_isleri_src.storage")
screener = importlib.import_module("borsa_isleri_src.screener")
universe = importlib.import_module("borsa_isleri_src.universe")

st.title("Fırsat Taraması")
render_last_update_banner(storage)
st.caption(
    "Uzun süredir ucuz (52 haftalık dibe yakın) VE yatayda kalmış sembolleri "
    "tüm kategorilerde tarar. **Yatırım tavsiyesi değildir** — adayları "
    "inceleyip kararı sen verirsin."
)

name_map: dict[str, str] = dict(config.SYMBOL_NAMES)
name_map.update(universe.get_nasdaq100_name_map())
name_map.update(universe.get_snp500_name_map())

CATEGORY_LABELS = {
    "bist100": "BIST 100",
    "diger_bist": "Diğer Hisseler",
    "emtia": "Emtia & Döviz",
    "crypto": "Kripto",
    "nasdaq100": "Nasdaq-100",
    "snp500": "S&P 500",
}

conn = storage.get_connection()
db_symbols = set(storage.all_symbols_in_db(conn))

pairs: list[tuple[str, str]] = []
for group, symbols in config.TICKERS.items():
    label = CATEGORY_LABELS.get(group, group)
    pairs.extend((s, label) for s in symbols if s in db_symbols)

for symbol in universe.get_nasdaq100_symbols():
    if symbol in db_symbols:
        pairs.append((symbol, CATEGORY_LABELS["nasdaq100"]))

for symbol in universe.get_snp500_symbols():
    if symbol in db_symbols:
        pairs.append((symbol, CATEGORY_LABELS["snp500"]))

if not pairs:
    conn.close()
    st.warning(
        "Veritabanında henüz veri yok. Önce şunu çalıştır:\n\n"
        "`borsa-isleri\\.venv\\Scripts\\python.exe borsa-isleri\\scripts\\run_fetch.py`"
    )
    st.stop()

with st.spinner(f"{len(pairs)} sembol taranıyor..."):
    result = screener.screen_symbols(pairs, storage, conn)
conn.close()

if result.empty:
    st.info("Yeterli geçmiş veri olan sembol bulunamadı.")
    st.stop()

col1, col2, col3 = st.columns(3)
col1.metric("Taranan Sembol", len(result))
col2.metric("Aday Bulundu", int(result["aday_mi"].sum()))
col3.metric("Kategori Sayısı", result["kategori"].nunique())

only_candidates = st.checkbox("Sadece adayları göster", value=True)
category_filter = st.multiselect(
    "Kategori filtrele", options=sorted(result["kategori"].unique()), default=[]
)

filtered = result
if only_candidates:
    filtered = filtered[filtered["aday_mi"]]
if category_filter:
    filtered = filtered[filtered["kategori"].isin(category_filter)]

filtered = add_name_column(filtered, name_map)
st.dataframe(rename_for_display(filtered), use_container_width=True, hide_index=True)
