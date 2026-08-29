"""Çalışma Ortamı — tek menü, birden fazla proje.

Bu, tüm projelerin (borsa-isleri, kurum-scriptleri/... ve ilerideki yenileri)
tek bir Streamlit uygulaması içinde, sol menüden erişilebildiği merkezi
arayüzdür. Menünün klasör/sıra yapısı `menu_config.json` içinde tutulur ve
sol menüdeki "Menü Yönetimi" sayfasından düzenlenir (yeni klasör, taşıma,
sıralama, menüden kaldırma).

Çalıştırmak için proje kökünden (scriptler/):
    workspace\\.venv\\Scripts\\python.exe -m streamlit run workspace\\Home.py

Yeni bir proje eklemek için `project_loader.py` içindeki talimatlara bak.
"""

import streamlit as st

from menu_store import build_navigation, load_items

st.set_page_config(page_title="Çalışma Ortamı", layout="wide")

items = load_items()
nav = build_navigation(items)

pg = st.navigation(nav)
pg.run()
