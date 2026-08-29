"""Fırsat Taraması — tüm kategorileri (BIST100, Diğer Hisseler, Emtia,
Nasdaq-100, S&P 500, Kripto) birlikte tarar. İki farklı bakış açısı sunar:
"Fiyat Bazlı Fırsat" (52 hafta dip/yatay/RSI) ve "Grafik Fırsatı" (dolar
bazında 2-5 yıl önceki seviyeye gerileme + zirveden ciddi düşüş + yatay).

Not: Bu YATIRIM TAVSİYESİ değildir — sadece dikkat çekici adayları filtreler,
karar ve inceleme kullanıcıya aittir.
"""

import importlib
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

WORKSPACE_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = WORKSPACE_DIR.parent

sys.path.insert(0, str(WORKSPACE_DIR))
from project_loader import load_project_package  # noqa: E402
from borsa_category_view import render_favoritable_table, render_last_update_banner  # noqa: E402

load_project_package("borsa_isleri_src", ROOT_DIR / "borsa-isleri" / "src")
config = importlib.import_module("borsa_isleri_src.config")
storage = importlib.import_module("borsa_isleri_src.storage")
screener = importlib.import_module("borsa_isleri_src.screener")
universe = importlib.import_module("borsa_isleri_src.universe")
favorites = importlib.import_module("borsa_isleri_src.favorites")

st.title("Fırsat Taraması")
render_last_update_banner(storage)

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

# --- Hisselerim (tüm kategoriler) ---
st.subheader("⭐ Hisselerim (tüm kategoriler)")
current_favorites = favorites.load_favorites()
if not current_favorites:
    st.caption("Henüz favori eklemedin — aşağıdaki tablolarda ⭐ Favori kutucuğunu işaretleyerek ekleyebilirsin.")
else:
    fav_rows = []
    for symbol, kategori in current_favorites.items():
        price_df = storage.read_prices(conn, symbol)
        if price_df.empty:
            continue
        fav_rows.append({"symbol": symbol, "kategori": kategori, "current_price": float(price_df.iloc[-1]["close"])})
    render_favoritable_table(pd.DataFrame(fav_rows), name_map, favorites, key_prefix="hisselerim_tumu")

with st.spinner(f"{len(pairs)} sembol taranıyor (iki yöntemle)..."):
    price_result = screener.screen_symbols(pairs, storage, conn)
    chart_result = screener.screen_chart_opportunities(pairs, storage, conn)
conn.close()

tab_price, tab_chart = st.tabs(["Fiyat Bazlı Fırsat", "Grafik Fırsatı"])

with tab_price:
    st.caption(
        "Uzun süredir ucuz (52 haftalık dibe yakın) VE yatayda kalmış sembolleri "
        "işaretler. **Yatırım tavsiyesi değildir.**"
    )
    if price_result.empty:
        st.info("Yeterli geçmiş veri olan sembol bulunamadı.")
    else:
        col1, col2, col3 = st.columns(3)
        col1.metric("Taranan Sembol", len(price_result))
        col2.metric("Aday Bulundu", int(price_result["aday_mi"].sum()))
        col3.metric("Kategori Sayısı", price_result["kategori"].nunique())

        only_candidates = st.checkbox("Sadece adayları göster", value=True, key="price_only_candidates")
        category_filter = st.multiselect(
            "Kategori filtrele", options=sorted(price_result["kategori"].unique()), default=[], key="price_cat_filter"
        )

        filtered = price_result
        if only_candidates:
            filtered = filtered[filtered["aday_mi"]]
        if category_filter:
            filtered = filtered[filtered["kategori"].isin(category_filter)]

        render_favoritable_table(filtered, name_map, favorites, key_prefix="price_tumu")

with tab_chart:
    st.caption(
        "Temel verilerden (defter değeri vb.) bağımsız, sadece fiyat grafiğine "
        "bakar: dolar bazında 2 veya 5 yıl önceki seviyesine gerilemiş, "
        "zirveden ciddi düşmüş VE şu an yatayda olan sembolleri işaretler. "
        "BIST hisseleri için TL fiyatı otomatik dolara çevrilir. "
        "**Yatırım tavsiyesi değildir.**"
    )
    if chart_result.empty:
        st.info("Yeterli geçmiş veri olan sembol bulunamadı (en az ~2 yıllık veri önerilir).")
    else:
        col1, col2, col3 = st.columns(3)
        col1.metric("Taranan Sembol", len(chart_result))
        col2.metric("Aday Bulundu", int(chart_result["aday_mi"].sum()))
        col3.metric("Kategori Sayısı", chart_result["kategori"].nunique())

        only_candidates_c = st.checkbox("Sadece adayları göster", value=True, key="chart_only_candidates")
        category_filter_c = st.multiselect(
            "Kategori filtrele", options=sorted(chart_result["kategori"].unique()), default=[], key="chart_cat_filter"
        )

        filtered_c = chart_result
        if only_candidates_c:
            filtered_c = filtered_c[filtered_c["aday_mi"]]
        if category_filter_c:
            filtered_c = filtered_c[filtered_c["kategori"].isin(category_filter_c)]

        render_favoritable_table(filtered_c, name_map, favorites, key_prefix="chart_tumu")
