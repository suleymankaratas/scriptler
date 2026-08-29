"""Çalışma Ortamı — tek menü, birden fazla proje.

Bu, tüm projelerin (borsa-isleri, kurum-scriptleri/... ve ilerideki yenileri)
tek bir Streamlit uygulaması içinde, sol menüden erişilebildiği merkezi
arayüzdür.

Çalıştırmak için proje kökünden (scriptler/):
    workspace\\.venv\\Scripts\\python.exe -m streamlit run workspace\\Home.py

Yeni bir proje eklemek için `project_loader.py` içindeki talimatlara bak.
"""

import streamlit as st

st.set_page_config(page_title="Çalışma Ortamı", layout="wide")

st.title("Çalışma Ortamı")
st.write("Sol menüden mevcut projeler arasında geçiş yapabilirsin.")

st.subheader("Mevcut Projeler")
st.markdown(
    "- **Borsa Takip** — BIST/döviz-emtia/kripto/global piyasa verisi ve grafik\n"
    "- **Router Arıza Kontrol** — kurum router'larının erişilebilirlik kontrolü"
)
