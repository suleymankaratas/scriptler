"""Kategori bazlı borsa sayfaları (BIST 100, Nasdaq-100, S&P 500 vb.) için
ortak render fonksiyonu — 6 kategori sayfasının hepsi bunu çağırır, kod
tekrarını önler.
"""

import datetime as dt
import time

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Aralık grupları (diğer finans platformlarındaki gibi: Dakika/Saat/Gün).
# Her seçenek: period/interval (yfinance) + resample (Yahoo'da native olmayan
# aralıklar için, daha ince bir veriden pandas ile hesaplanır).
#
# Yahoo Finance'in gerçek kısıtları (ücretsiz kaynak, değiştiremeyiz):
#  - 1 dakikalık veri: sadece son 7 gün
#  - 2-30 dakikalık veri: sadece son ~60 gün
#  - Saatlik veri: sadece son ~2 yıl
#  - Günlük ve üzeri: uzun geçmiş (5 yıl / mevcut olabildiğince "max")
INTERVAL_GROUPS: dict[str, dict[str, dict]] = {
    "Dakika": {
        "1 Dakika": {"period": "7d", "interval": "1m", "resample": None},
        "2 Dakika": {"period": "60d", "interval": "2m", "resample": None},
        "3 Dakika": {"period": "7d", "interval": "1m", "resample": "3min"},
        "5 Dakika": {"period": "60d", "interval": "5m", "resample": None},
        "10 Dakika": {"period": "60d", "interval": "5m", "resample": "10min"},
        "15 Dakika": {"period": "60d", "interval": "15m", "resample": None},
        "30 Dakika": {"period": "60d", "interval": "30m", "resample": None},
        "45 Dakika": {"period": "60d", "interval": "15m", "resample": "45min"},
    },
    "Saat": {
        "1 Saat": {"period": "2y", "interval": "1h", "resample": None},
        "2 Saat": {"period": "2y", "interval": "1h", "resample": "2h"},
        "3 Saat": {"period": "2y", "interval": "1h", "resample": "3h"},
        "4 Saat": {"period": "2y", "interval": "1h", "resample": "4h"},
    },
    "Gün": {
        "1 Gün": {"period": "5y", "interval": "1d", "resample": None, "from_db": True},
        "1 Hafta": {"period": "5y", "interval": "1wk", "resample": None},
        "1 Ay": {"period": "5y", "interval": "1mo", "resample": None},
        "3 Ay": {"period": "max", "interval": "3mo", "resample": None},
        "6 Ay": {"period": "max", "interval": "1mo", "resample": "6ME"},
        "12 Ay": {"period": "max", "interval": "1mo", "resample": "12ME"},
    },
}

# Tablo sütun adlarını okunur Türkçe başlıklara çeviren ortak eşleme.
DISPLAY_COLUMNS = {
    "sira": "Sıra",
    "symbol": "Sembol",
    "sirket_adi": "Şirket Adı",
    "kategori": "Kategori",
    "current_price": "Güncel Fiyat",
    "pct_from_52w_low": "52 Hafta Dibinden %",
    "pct_from_52w_high": "52 Hafta Zirvesinden %",
    "sideways_range_pct": "Yatay Bant %",
    "rsi": "RSI",
    "aday_mi": "Aday mı?",
    "aciklama": "Açıklama",
    "current_price_usd": "Güncel Fiyat (USD)",
    "vs_2 yıl": "2 Yıl Önceye Göre % (USD)",
    "vs_5 yıl": "5 Yıl Önceye Göre % (USD)",
    "drawdown_from_peak_pct": "Zirveden Uzaklık % (USD)",
    "date": "Tarih",
    "open": "Açılış",
    "high": "Yüksek",
    "low": "Düşük",
    "close": "Kapanış",
    "volume": "Hacim",
}


def rename_for_display(df: pd.DataFrame) -> pd.DataFrame:
    """DataFrame sütunlarını okunur Türkçe başlıklara çevirir (sadece
    görüntüleme için — mantıkta orijinal isimler kullanılmaya devam eder).
    """
    return df.rename(columns=DISPLAY_COLUMNS)


def add_name_column(df: pd.DataFrame, name_map: dict[str, str]) -> pd.DataFrame:
    """"symbol" sütununun hemen yanına "sirket_adi" (şirket/varlık adı) sütunu ekler."""
    if df.empty or "symbol" not in df.columns:
        return df
    df = df.copy()
    df.insert(1, "sirket_adi", df["symbol"].map(name_map).fillna(""))
    return df


def _resample_ohlcv(df: pd.DataFrame, rule: str) -> pd.DataFrame:
    resampled = df.resample(rule).agg(
        {"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}
    )
    # Piyasa kapalıyken (gece, hafta sonu) oluşan boş zaman dilimlerinde
    # Volume=0 olur ama fiyat NaN kalır — how="all" bunları elemez, bu yüzden
    # Close'a göre eleriz (fetch.py'deki aynı desen, bkz. fetch_many_bulk).
    return resampled[resampled["Close"].notna()]


def _normalize_columns(raw: pd.DataFrame) -> pd.DataFrame:
    df = raw.reset_index()
    date_col = df.columns[0]
    df = df.rename(
        columns={
            date_col: "date", "Open": "open", "High": "high",
            "Low": "low", "Close": "close", "Volume": "volume",
        }
    )
    return df[["date", "open", "high", "low", "close", "volume"]]


@st.cache_data(ttl=60, show_spinner=False)
def _fetch_live(_fetch, symbol: str, period: str, interval: str, resample_rule: str | None):
    """Tek bir sembol için canlıya en yakın veriyi çeker (60 sn önbellekli —
    her etkileşimde Yahoo'ya gitmemek için, ama "Şimdi Yenile" ile anında
    tazelenebilir). Modül argümanları (_fetch) Streamlit'in cache anahtarına
    dahil edilmez (başına _ konan argümanlar hash'lenmez).
    """
    raw = _fetch.fetch_history(symbol, period=period, interval=interval)
    if raw.empty:
        return pd.DataFrame(), time.time()
    if resample_rule:
        raw = _resample_ohlcv(raw, resample_rule)
    return _normalize_columns(raw), time.time()


def _load_chart_data(symbol: str, group: str, label: str, storage, fetch, conn):
    """Seçilen aralığa göre veriyi (df, veri_zamani) olarak döner.

    "1 Gün" için zaten toplu çekilmiş SQLite verisi kullanılır (network
    gerekmez). Diğer tüm aralıklar (haftalık/aylık/saatlik/dakikalık) sadece
    incelenen bu tek sembol için canlı çekilir.
    """
    opts = INTERVAL_GROUPS[group][label]

    if opts.get("from_db"):
        return storage.read_prices(conn, symbol), None

    df, fetched_at = _fetch_live(fetch, symbol, opts["period"], opts["interval"], opts["resample"])
    return df, fetched_at


def _matches_search(symbol: str, name_map: dict[str, str], query: str) -> bool:
    q = query.strip().casefold()
    if not q:
        return True
    return q in symbol.casefold() or q in name_map.get(symbol, "").casefold()


def render_ranked_table(df: pd.DataFrame, name_map: dict[str, str], key_prefix: str) -> str | None:
    """Arama kutusu + sıralı, salt-okunur, TIKLANABİLİR bir tablo çizer.

    Bir satıra tıklanınca o satırın sembolünü döner (tıklama yoksa None) —
    çağıran taraf bunu "Sembol İncele / Ayrıntılı Analiz" panelini o sembole
    çevirmek için kullanır. Favori işaretleme burada değil, detay panelinde
    yapılır (aynı tabloda hem tıkla-seç hem düzenlenebilir kutucuk sağlıklı
    çalışmıyor).
    """
    if df.empty:
        st.dataframe(rename_for_display(df), use_container_width=True, hide_index=True)
        return None

    df = df if "sirket_adi" in df.columns else add_name_column(df, name_map)
    df = df.reset_index(drop=True)

    query = st.text_input(
        "🔍 Ara (sembol veya şirket adı)", key=f"search_{key_prefix}", placeholder="örn. THYAO veya Türk Hava"
    )
    if query:
        mask = df["symbol"].apply(lambda s: _matches_search(s, name_map, query))
        df = df[mask].reset_index(drop=True)

    if df.empty:
        st.caption("Arama sonucunda sembol bulunamadı.")
        return None

    display_df = df.copy()
    if "aday_mi" in display_df.columns:
        # Bilgi amaçlı, salt-okunur bir sonuç sütunu — boolean bırakırsak
        # Streamlit checkbox gibi gösteriyor, tıklanabilir satırla karışmasın
        # diye düz metne çeviriyoruz.
        display_df["aday_mi"] = display_df["aday_mi"].map({True: "✅ Evet", False: "—"})
    display_df = rename_for_display(display_df)

    st.caption("👆 Ayrıntılı analiz için bir satıra tıkla.")
    event = st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key=f"table_{key_prefix}",
    )

    selected_rows = event.selection.rows if event and event.selection else []
    if selected_rows:
        return df.loc[selected_rows[0], "symbol"]
    return None


def _build_price_figure(df: pd.DataFrame, tech: dict | None) -> go.Figure:
    """Kapanış fiyatı çizgisi + (varsa) destek/direnç/Fibonacci referans
    çizgileriyle bir Plotly grafiği kurar.
    """
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(x=df["date"], y=df["close"], mode="lines", name="Kapanış", line=dict(color="#2563eb", width=2))
    )

    if tech:
        for lvl in tech.get("support_levels", []):
            fig.add_hline(
                y=lvl, line_dash="dot", line_color="#16a34a",
                annotation_text=f"Destek {lvl:.2f}", annotation_position="bottom right",
            )
        for lvl in tech.get("resistance_levels", []):
            fig.add_hline(
                y=lvl, line_dash="dot", line_color="#dc2626",
                annotation_text=f"Direnç {lvl:.2f}", annotation_position="top right",
            )
        for label, lvl in (tech.get("fibonacci_levels") or {}).items():
            fig.add_hline(
                y=lvl, line_dash="dash", line_color="#a855f7", opacity=0.35,
                annotation_text=f"Fib {label}", annotation_position="left",
            )

    fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=440, showlegend=False)
    return fig


def render_symbol_detail(
    symbol: str,
    category_label: str,
    name_map: dict[str, str],
    storage,
    fetch,
    favorites,
    analysis,
    key_prefix: str,
) -> None:
    """Tek bir sembol için: favori aç/kapa, aralık seçici + grafik (destek/
    direnç/Fibonacci işaretli), ve yazılı teknik analiz yorumu.
    """
    display_name = name_map.get(symbol, "")
    st.markdown(f"#### {symbol}" + (f" — {display_name}" if display_name else ""))

    current_favorites = favorites.load_favorites()
    is_fav = symbol in current_favorites

    col_fav, col_group, col_value, col_refresh = st.columns([1.3, 1.3, 1.5, 1])
    with col_fav:
        new_fav = st.checkbox("⭐ Favorilerde", value=is_fav, key=f"favtoggle_{key_prefix}_{symbol}")
        if new_fav != is_fav:
            favorites.set_favorite(symbol, category_label, new_fav)
            st.rerun()
    with col_group:
        group = st.radio("Grup", options=list(INTERVAL_GROUPS.keys()), horizontal=True, key=f"group_{key_prefix}")
    with col_value:
        label = st.selectbox("Aralık", options=list(INTERVAL_GROUPS[group].keys()), key=f"interval_{group}_{key_prefix}")
    with col_refresh:
        st.write("")
        if st.button("🔄 Şimdi Yenile", key=f"refresh_{key_prefix}"):
            _fetch_live.clear()

    conn = storage.get_connection()
    with st.spinner("Veri hazırlanıyor..."):
        df, fetched_at = _load_chart_data(symbol, group, label, storage, fetch, conn)

    if df.empty:
        conn.close()
        st.info(
            "Bu sembol/aralık için veri bulunamadı (Yahoo Finance bu aralıkta "
            "veri sunmuyor olabilir — özellikle dakikalık veriler için işlem "
            "saatleri dışında veya çok yeni/az işlem gören semboller)."
        )
        return

    if fetched_at is not None:
        st.caption(f"⏱ Bu grafik canlı çekildi: {dt.datetime.fromtimestamp(fetched_at).strftime('%H:%M:%S')}")

    is_try = symbol.endswith(".IS")
    usdtry_df = storage.read_prices(conn, "USDTRY=X") if is_try else None
    tech = analysis.analyze_symbol(df, is_try_denominated=is_try, usdtry_df=usdtry_df)
    conn.close()

    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader(f"Kapanış Fiyatı ({label})")
        st.plotly_chart(_build_price_figure(df, tech), use_container_width=True, key=f"chart_{key_prefix}")
    with col2:
        last_row = df.iloc[-1]
        st.metric("Son Kapanış", f"{last_row['close']:.2f}")
        if len(df) > 1:
            prev_close = df.iloc[-2]["close"]
            change_pct = (last_row["close"] - prev_close) / prev_close * 100
            st.metric("Değişim (son bar)", f"{change_pct:+.2f}%")

    st.subheader("Teknik Analiz Yorumu")
    if tech:
        st.info(tech["yorum"])
    else:
        st.caption("Ayrıntılı teknik analiz için yeterli geçmiş veri yok (en az ~30 gün gerekir).")

    st.subheader("Veri Tablosu")
    st.dataframe(
        rename_for_display(df.sort_values("date", ascending=False)),
        use_container_width=True,
        hide_index=True,
    )


def render_last_update_banner(storage) -> None:
    """Toplu (günlük) verinin en son ne zaman çekildiğini gösterir."""
    info = storage.read_last_fetch_info()
    if not info:
        st.caption("Son toplu veri güncellemesi bilgisi yok (henüz run_fetch.py çalıştırılmamış).")
        return
    fetched_at = dt.datetime.fromtimestamp(info["fetched_at"])
    st.caption(
        f"📅 Son toplu veri güncellemesi: **{fetched_at.strftime('%d.%m.%Y %H:%M')}** "
        f"({info['symbol_count']} sembol, {info['row_count']} satır) — "
        "günlük fiyatlar bu tarihten itibaren güncel değilse `run_fetch.py`'yi tekrar çalıştır."
    )


def render_category_page(
    title: str, symbols: list[str], config, storage, screener, fetch, favorites, analysis, name_map: dict | None = None
) -> None:
    st.title(title)
    render_last_update_banner(storage)

    name_map = name_map or config.SYMBOL_NAMES

    conn = storage.get_connection()
    db_symbols = set(storage.all_symbols_in_db(conn))
    available = [s for s in symbols if s in db_symbols]
    conn.close()

    if not available:
        st.warning(
            "Bu kategori için veritabanında henüz veri yok. Önce şunu çalıştır:\n\n"
            "`borsa-isleri\\.venv\\Scripts\\python.exe borsa-isleri\\scripts\\run_fetch.py`"
        )
        return

    session_key = f"selected_symbol_{title}"
    if session_key not in st.session_state or st.session_state[session_key] not in available:
        st.session_state[session_key] = available[0]

    # --- Hisselerim ---
    st.subheader("⭐ Hisselerim (bu kategori)")
    current_favorites = favorites.load_favorites()
    fav_symbols = [s for s in available if s in current_favorites]
    if not fav_symbols:
        st.caption(
            "Henüz bu kategoriden favori eklemedin — bir sembolün ayrıntılı "
            "analiz panelinden ⭐ Favorilerde kutucuğunu işaretleyerek ekleyebilirsin."
        )
    else:
        conn = storage.get_connection()
        rows = []
        for symbol in fav_symbols:
            price_df = storage.read_prices(conn, symbol)
            if price_df.empty:
                continue
            rows.append(
                {
                    "symbol": symbol,
                    "kategori": current_favorites.get(symbol, title),
                    "current_price": float(price_df.iloc[-1]["close"]),
                }
            )
        conn.close()
        clicked = render_ranked_table(pd.DataFrame(rows), name_map, key_prefix=f"hisselerim_{title}")
        if clicked:
            st.session_state[session_key] = clicked

    # --- Fırsat Taraması ---
    st.subheader("Fırsat Taraması (bu kategori)")
    st.caption(
        "Uzun süredir ucuz (52 haftalık dibe yakın) VE yatayda kalmış "
        "sembolleri işaretler. Sıra, TÜM sembolleri en avantajlıdan en "
        "avantajsıza sıralar. Yatırım tavsiyesi değildir."
    )
    conn = storage.get_connection()
    pairs = [(s, title) for s in available]
    result = screener.screen_symbols(pairs, storage, conn)
    if result.empty:
        st.info("Yeterli geçmiş veri olan sembol bulunamadı (en az ~1 aylık veri gerekir).")
    else:
        candidate_count = int(result["aday_mi"].sum())
        st.caption(f"{len(result)} sembol tarandı, {candidate_count} aday bulundu.")
        clicked = render_ranked_table(result, name_map, key_prefix=f"price_{title}")
        if clicked:
            st.session_state[session_key] = clicked

    # --- Grafik Fırsatı ---
    st.subheader("Grafik Fırsatı (bu kategori)")
    st.caption(
        "Temel verilerden (defter değeri vb.) bağımsız, sadece fiyat grafiğine "
        "bakar: dolar bazında 2 veya 5 yıl önceki seviyesine gerilemiş, "
        "zirveden ciddi düşmüş VE şu an yatayda olan sembolleri işaretler. "
        "BIST hisseleri için TL fiyatı otomatik dolara çevrilir. Yatırım "
        "tavsiyesi değildir."
    )
    chart_result = screener.screen_chart_opportunities(pairs, storage, conn)
    conn.close()
    if chart_result.empty:
        st.info("Yeterli geçmiş veri olan sembol bulunamadı (en az ~2 yıllık veri önerilir).")
    else:
        chart_candidate_count = int(chart_result["aday_mi"].sum())
        st.caption(f"{len(chart_result)} sembol tarandı, {chart_candidate_count} aday bulundu.")
        clicked = render_ranked_table(chart_result, name_map, key_prefix=f"chart_{title}")
        if clicked:
            st.session_state[session_key] = clicked

    # --- Sembol İncele / Ayrıntılı Analiz ---
    st.subheader("Sembol İncele / Ayrıntılı Analiz")
    st.caption("Yukarıdaki tablolardan bir satıra tıkla, ya da doğrudan buradan sembol seç.")
    manual_choice = st.selectbox(
        "Sembol",
        options=available,
        format_func=lambda s: f"{s} — {name_map.get(s, '')}" if name_map.get(s) else s,
        key=session_key,
    )

    render_symbol_detail(manual_choice, title, name_map, storage, fetch, favorites, analysis, key_prefix=f"detail_{title}")
