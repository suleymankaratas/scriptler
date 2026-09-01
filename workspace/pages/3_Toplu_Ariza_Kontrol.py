"""Toplu Arıza Kontrol sayfası — toplu_ariza_kontrol/ariza_kontrol.py'yi Streamlit'te kullanır."""

import sys
from pathlib import Path

import streamlit as st
import pandas as pd

WORKSPACE_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = WORKSPACE_DIR.parent
PROJECT_DIR = ROOT_DIR / "toplu_ariza_kontrol"

sys.path.insert(0, str(PROJECT_DIR))
sys.path.insert(0, str(WORKSPACE_DIR))

import ariza_kontrol

st.set_page_config(page_title="Toplu Arıza Kontrol", layout="wide")
st.title("📊 Toplu Arıza Kontrol")

st.markdown("""
Router'ları Excel dosyasından yükleyebilir veya tablodan ekleyebilirsiniz.
Sistem Telnet üzerinden VLAN internet erişimi, DHCP option43, WLC/EBA erişimi, 
ARP tablosu ve donanım durumunu kontrol eder.
""")

# ============================================================================
# Session state başlat
# ============================================================================
if "router_listesi" not in st.session_state:
    st.session_state.router_listesi = []

if "kontrol_sonuclari" not in st.session_state:
    st.session_state.kontrol_sonuclari = None

# ============================================================================
# 1. Router Bilgileri Tablosu
# ============================================================================
st.subheader("1️⃣ Router Bilgileri")

# Excel dosyasından yükle butonu
col_excel, col_spacer = st.columns([1, 4])
with col_excel:
    if st.button("📥 Excel'den Yükle", use_container_width=True):
        try:
            excel_path = PROJECT_DIR / "ariza_listesi.xlsx"
            df_excel = pd.read_excel(excel_path)
            
            # IP Adresi sütununu bul
            ip_col = None
            for col in df_excel.columns:
                if "IP" in str(col).upper():
                    ip_col = col
                    break
            
            if ip_col:
                # Excel verilerini session_state'e yükle
                routers = []
                for idx, row in df_excel.iterrows():
                    ip = str(row.get(ip_col, "")).strip()
                    if ip and ip.lower() != "nan":
                        aciklama = str(row.get("Okul / Aciklama", "")).strip()
                        kullanici = str(row.get("Kullanici Adi", "")).strip()
                        sifre = str(row.get("Sifre", "")).strip()
                        
                        routers.append({
                            "IP Adresi": ip,
                            "Kullanıcı Adı": kullanici if kullanici and kullanici.lower() != "nan" else "",
                            "Şifre": sifre if sifre and sifre.lower() != "nan" else "",
                            "Açıklama": aciklama if aciklama and aciklama.lower() != "nan" else ""
                        })
                
                st.session_state.router_listesi = routers
                st.success(f"✅ Excel'den {len(routers)} router yüklendi!")
                st.rerun()
            else:
                st.error("❌ 'IP Adresi' sütunu bulunamadı")
        except Exception as e:
            st.error(f"❌ Dosya okuma hatası: {e}")

st.markdown("---")

# Varsayılan kimlik bilgileri
col1, col2, col3 = st.columns(3)
with col1:
    default_username = st.text_input(
        "Varsayılan Kullanıcı Adı",
        value=ariza_kontrol.VARSAYILAN_KULLANICI_ADI,
        type="password",
        key="default_username"
    )
with col2:
    default_password = st.text_input(
        "Varsayılan Şifre",
        value=ariza_kontrol.VARSAYILAN_SIFRE,
        type="password",
        key="default_password"
    )
with col3:
    timeout = st.slider("Timeout (saniye)", min_value=5, max_value=30, value=10, key="timeout")

st.markdown("---")

# Router listesi tablosu
st.markdown("**Router Tablosu** (Sütunlar: IP Adresi, Kullanıcı Adı, Şifre, Açıklama)")

# Düzenlenebilir tablo
df_routers = pd.DataFrame(st.session_state.router_listesi, columns=["IP Adresi", "Kullanıcı Adı", "Şifre", "Açıklama"])
if df_routers.empty:
    df_routers = pd.DataFrame(columns=["IP Adresi", "Kullanıcı Adı", "Şifre", "Açıklama"])

edited_df = st.data_editor(
    df_routers,
    num_rows="dynamic",
    use_container_width=True,
    key="router_table",
    hide_index=True
)

# Session state'i güncelle
st.session_state.router_listesi = edited_df.to_dict("records")

# Boş satırları temizle (NaN değerleri hariç tut)
st.session_state.router_listesi = [
    r for r in st.session_state.router_listesi 
    if r.get("IP Adresi") and str(r.get("IP Adresi", "")).strip()
]

st.info(f"📌 Tabloda {len(st.session_state.router_listesi)} router tanımlandı")

# ============================================================================
# 2. Kontrol başlatma
# ============================================================================
st.subheader("2️⃣ Kontrolleri Çalıştır")

col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    if st.button("🚀 Tüm Router'ları Kontrol Et", type="primary", use_container_width=True):
        if not st.session_state.router_listesi:
            st.error("❌ Lütfen en az bir router tanımlayın")
        else:
            st.info(f"⏳ {len(st.session_state.router_listesi)} router kontrol ediliyor...")
            
            progress_bar = st.progress(0)
            results = []
            
            with st.spinner("Kontroller çalışıyor..."):
                for idx, router_info in enumerate(st.session_state.router_listesi, 1):
                    ip = str(router_info.get("IP Adresi", "") or "").strip()
                    username = str(router_info.get("Kullanıcı Adı", "") or "").strip() or default_username
                    password = str(router_info.get("Şifre", "") or "").strip() or default_password
                    aciklama = str(router_info.get("Açıklama", "") or "").strip()
                    
                    if not ip:
                        continue
                    
                    # 1. Kontrol et
                    result = ariza_kontrol.kontrol_et(ip, username, password, timeout=timeout)
                    result["ip"] = ip
                    result["aciklama"] = aciklama
                    
                    # 2. Özet çıkar
                    result["ozet"] = ariza_kontrol.ozet_cikar(result)
                    
                    results.append(result)
                    
                    # İlerleme göster
                    progress_bar.progress(idx / len(st.session_state.router_listesi))
            
            st.session_state.kontrol_sonuclari = results
            st.success(f"✅ {len(results)} router kontrol tamamlandı!")

# ============================================================================
# 3. Sonuçları göster
# ============================================================================
if st.session_state.kontrol_sonuclari:
    results = st.session_state.kontrol_sonuclari
    
    st.subheader("3️⃣ Sonuçlar")
    
    # Özet istatistikler
    col1, col2, col3, col4 = st.columns(4)
    
    total = len(results)
    erisim_ok = sum(1 for r in results if r["erisim"] and r["erisim"].startswith("ERISIM VAR"))
    sorun_yok = sum(1 for r in results if r["ozet"] == "Sorun yok")
    ariza = total - erisim_ok
    
    col1.metric("Toplam", total)
    col2.metric("Erişim OK", erisim_ok, delta_color="off")
    col3.metric("Sorun Yok", sorun_yok, delta_color="off")
    col4.metric("Arızalı/Erişim Yok", ariza, delta_color="inverse")
    
    st.markdown("---")
    
    # Detaylı tablo
    st.markdown("#### Özet Tablo")
    
    # DataFrame oluştur
    df_results = []
    for r in results:
        erisim_status = "✅" if r["erisim"].startswith("ERISIM VAR") else "❌"
        
        # VLAN sonuçlarını kısa göster
        vlan_status = []
        for vlan_no in [10, 11, 20, 30, 40, 50, 60]:
            vlan_sonuc = r["vlan_sonuclari"].get(vlan_no, "")
            if vlan_sonuc == "VAR":
                vlan_status.append(f"V{vlan_no}✅")
            elif vlan_sonuc == "YOK":
                vlan_status.append(f"V{vlan_no}❌")
        
        df_results.append({
            "IP": r["ip"],
            "Açıklama": r.get("aciklama", ""),
            "Okul": r.get("okul_adi", ""),
            "Erişim": erisim_status,
            "Marka": r.get("marka", ""),
            "VLAN İnt.": " ".join(vlan_status[:3]) if vlan_status else "-",
            "ARP": r.get("arp_sayisi", "?"),
            "WLC": "✅" if r.get("wlc_erisim") == "VAR" else "❌" if r.get("wlc_erisim") == "YOK" else "-",
            "EBA": "✅" if r.get("eba_erisim") == "VAR" else "❌" if r.get("eba_erisim") == "YOK" else "-",
            "Durumu": "🟢" if r["ozet"] == "Sorun yok" else "🔴"
        })
    
    df = pd.DataFrame(df_results)
    st.dataframe(df, use_container_width=True, height=300)
    
    st.markdown("---")
    
    # Detaylı görünüm
    st.markdown("#### Detay İnceleme")
    
    selected_ip = st.selectbox(
        "IP seçin:",
        options=[r["ip"] for r in results],
        format_func=lambda ip: f"{ip} - {next((r.get('aciklama', '') or r.get('okul_adi', '')) for r in results if r['ip'] == ip)}"
    )
    
    if selected_ip:
        result = next(r for r in results if r["ip"] == selected_ip)
        
        # Renk kodu: Sorun yok = yeşil, Sorun var = kırmızı
        if result["ozet"] == "Sorun yok":
            st.success(f"🟢 **{result['ip']}** - Sorun Yok")
        else:
            st.error(f"🔴 **{result['ip']}** - Sorun Bulundu")
        
        # Temel bilgiler
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write("**Temel Bilgiler**")
            st.write(f"• **Açıklama:** {result.get('aciklama', '-')}")
            st.write(f"• **Okul/Adı:** {result.get('okul_adi', 'N/A')}")
            st.write(f"• **Erişim:** {result['erisim']}")
            st.write(f"• **Marka:** {result.get('marka', 'N/A')}")
        
        with col2:
            st.write("**İnternet Durumu**")
            for vlan_no, kisa_isim in ariza_kontrol.VLAN_KISA_ISIM.items():
                sonuc_metni = result["vlan_sonuclari"].get(vlan_no, "IP BULUNAMADI")
                icon = "✅" if sonuc_metni == "VAR" else "❌" if sonuc_metni == "YOK" else "⚠️"
                st.write(f"• {icon} **{kisa_isim}:** {sonuc_metni}")
        
        with col3:
            st.write("**Özel Kontroller**")
            st.write(f"• **ARP Cihaz:** {result.get('arp_sayisi', 'N/A')}")
            st.write(f"• **WLC:** {result.get('wlc_erisim', '-')}")
            st.write(f"• **EBA:** {result.get('eba_erisim', '-')}")
            st.write(f"• **NAT:** {'✅' if result.get('nat_calisiyor') else '❌'}")
            st.write(f"• **Harici Modem:** {'Var' if result.get('harici_modem') else 'Yok'}")
        
        st.divider()
        
        # Detaylı Özet
        st.write("**Kontrol Özeti**")
        st.info(result["ozet"])
        
        # DHCP Option43
        if result.get("dhcp_option_sonuclari"):
            st.divider()
            st.write("**DHCP Option43 (Kablosuz/AP)**")
            dhcp_kisa_isim = {1: "VLAN1", 10: "VLAN10"}
            for vlan_no, deger in result["dhcp_option_sonuclari"].items():
                icon = "✅" if deger == "VAR" else "❌" if deger == "YOK" else "⚠️"
                st.write(f"• {icon} {dhcp_kisa_isim.get(vlan_no, f'VLAN{vlan_no}')}: {deger}")
        
        # Donanım Durumu
        if result.get("donanim_alarm") is not None:
            st.divider()
            if result.get("donanim_alarm"):
                st.error("🔴 **Donanım/Kart Alarmi TESPIT EDİLDİ**")
                if result.get("alarm_seviye"):
                    st.write(f"• Seviye: {result['alarm_seviye']}")
                    st.write(f"• Toplam Alarm: {result['alarm_sayisi']}")
            else:
                st.success("🟢 Donanım Durumu: Normal")
else:
    st.info("💡 Router'ları tanımlayıp kontrol başlat butonuna basınız.")

st.divider()

col1, col2 = st.columns(2)

with col1:
    if st.button("🗑️ Sonuçları Temizle", use_container_width=True):
        st.session_state.kontrol_sonuclari = None
        st.rerun()

with col2:
    if st.button("📥 Router Listesini Temizle", use_container_width=True):
        st.session_state.router_listesi = []
        st.rerun()

st.caption("📌 Telnet bağlantısı sorunları:")
st.caption("• Router'da telnet portu (23) açık mı?")
st.caption("• Kullanıcı adı ve şifre doğru mu?")
st.caption("• Network bağlantısı var mı?")
