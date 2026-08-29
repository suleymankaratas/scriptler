"""Router Arıza Kontrol — arayüz.

Çalıştırmak için bu klasörden:
    streamlit run app.py --server.port 8502

(Borsa dashboard'u 8501'i kullandığı için burada farklı bir port önerilir,
ikisini aynı anda açık tutmak istersen.)
"""

from pathlib import Path

import streamlit as st

from config import LOG_PATH, ROUTERS
from runner import run_all_checks, setup_logging

st.set_page_config(page_title="Router Arıza Kontrol", layout="wide")
st.title("Router Arıza Kontrol")

st.caption(
    f"{len(ROUTERS)} hedef tanımlı. Gerçek router listesini `config.py` "
    "içinden düzenleyebilirsin."
)

if st.button("Şimdi Kontrol Et", type="primary"):
    setup_logging()
    with st.spinner("Kontroller çalışıyor..."):
        st.session_state["last_results"] = run_all_checks()

results = st.session_state.get("last_results")

if results is None:
    st.info("Henüz kontrol çalıştırılmadı. Yukarıdaki butona bas.")
else:
    ok_count = sum(1 for r in results if r["ok"])
    fail_count = len(results) - ok_count

    col1, col2, col3 = st.columns(3)
    col1.metric("Toplam Kontrol", len(results))
    col2.metric("Sorunsuz", ok_count)
    col3.metric("Arızalı", fail_count, delta=None)

    st.subheader("Sonuçlar")
    for r in results:
        icon = "🟢" if r["ok"] else "🔴"
        st.write(f"{icon} **{r['name']}** ({r['ip']}) — {r['check']}: {r['detail']}")

st.subheader("Log Dosyası (son satırlar)")
if LOG_PATH.exists():
    lines = Path(LOG_PATH).read_text(encoding="utf-8").splitlines()
    st.code("\n".join(lines[-30:]) or "(log boş)")
else:
    st.write("Henüz log dosyası oluşmadı.")
