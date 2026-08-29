# Router Arıza Kontrol

Kurumdaki router'ların erişilebilirliğini kontrol eden araç.

> Bu proje artık ana `workspace/` menüsünden ("Router Arıza Kontrol" sayfası)
> çalışıyor — bkz. kök [README.md](../../README.md). Aşağıdaki adımlar bu
> projeyi tek başına (bağımsız) çalıştırmak içindir.

**Durum:** İskelet/arayüz hazır, gerçek kontrol mantığı (ping'in ötesinde
port/SNMP kontrolleri vb.) başka bir bilgisayarda hazırlanıyor ve
buraya eklenecek. Şu an sadece basit bir ping kontrolü çalışır durumda —
`config.py`'deki `ROUTERS` listesine gerçek router'ları ekleyerek
kullanılabilir.

## Kurulum

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Kullanım

- **Komut satırından:** `python check_routers.py`
- **Arayüzden:** `streamlit run app.py --server.port 8502`
  (borsa dashboard'u 8501 kullandığı için farklı port önerilir)

## Yapı

- `config.py` — kontrol edilecek router listesi ve log dosyası yolu
- `checks.py` — kontrol fonksiyonları (şu an: `ping_check`); yeni kontrol
  türleri (port, SNMP) buraya eklenip `CHECKS` sözlüğüne kaydedilir
- `runner.py` — ortak çalıştırma mantığı (CLI ve arayüz bunu kullanır)
- `check_routers.py` — komut satırı girişi
- `app.py` — Streamlit arayüzü
- `logs/router_kontrol.log` — çalışma geçmişi (git'e dahil değil)

## Sonraki Adım

Diğer bilgisayardaki hazır script buraya eklenince: mantığı `checks.py`
içine yeni bir kontrol fonksiyonu olarak taşı, `config.py`'deki router
listesini gerçek IP'lerle doldur. Arayüz (`app.py`) ve CLI
(`check_routers.py`) değişiklik gerekmeden yeni kontrolleri otomatik
kullanır.
