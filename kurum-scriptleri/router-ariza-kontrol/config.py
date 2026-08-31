"""Router arıza kontrol ayarları.

ROUTERS listesine gerçek router'larını ekle. Her router için "checks"
alanı, checks.py içindeki CHECKS sözlüğünde tanımlı hangi kontrollerin
çalışacağını belirler (şu an sadece "ping" var; port/SNMP gibi yeni
kontrol türleri eklendikçe buraya da ekleyebilirsin).
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
LOG_PATH = BASE_DIR / "logs" / "router_kontrol.log"

# Şimdilik tek bir test hedefi (localhost, her zaman ayakta olması beklenir).
# Not: Bazı ağlar/sandbox ortamları dışa ICMP (ping) trafiğini engeller;
# bu durumda internet üzerindeki bir IP'ye (örn. 8.8.8.8) ping "arıza" gibi
# görünebilir. Gerçek LAN içindeki router'lar için bu genelde sorun olmaz.
# Gerçek router'larını eklerken aynı formatta yeni satırlar ekle.
ROUTERS = [
    {"name": "test-hedef (localhost)", "ip": "127.0.0.1", "checks": ["ping"]},
    # {"name": "sube1-router", "ip": "192.168.1.1", "checks": ["ping"]},
]
