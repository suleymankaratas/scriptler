"""Router kontrol fonksiyonları.

Yeni bir kontrol türü eklemek için:
1. Aşağıya `def xxx_check(ip: str) -> CheckResult` şeklinde bir fonksiyon ekle.
2. CHECKS sözlüğüne "xxx": xxx_check olarak kaydet.
3. config.py'deki ilgili router'ın "checks" listesine "xxx" ekle.

Örnek ileride eklenebilecek kontroller: port_check (belirli bir TCP portunun
açık olup olmadığı), snmp_check (SNMP ile CPU/interface durumu).
"""

import platform
import subprocess
from dataclasses import dataclass


@dataclass
class CheckResult:
    ok: bool
    detail: str


def ping_check(ip: str, timeout_ms: int = 1000) -> CheckResult:
    """ICMP ping ile erişilebilirlik kontrolü.

    Ekstra kütüphane veya yönetici (admin) yetkisi gerektirmemesi için
    işletim sisteminin kendi `ping` komutu kullanılır.
    """
    is_windows = platform.system().lower() == "windows"
    if is_windows:
        cmd = ["ping", "-n", "1", "-w", str(timeout_ms), ip]
    else:
        cmd = ["ping", "-c", "1", "-W", str(max(1, timeout_ms // 1000)), ip]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=(timeout_ms / 1000) + 2,
        )
    except subprocess.TimeoutExpired:
        return CheckResult(ok=False, detail="ping zaman aşımı")
    except FileNotFoundError:
        return CheckResult(ok=False, detail="ping komutu bulunamadı")

    ok = result.returncode == 0
    detail = "yanıt verdi" if ok else "yanıt vermedi"
    return CheckResult(ok=ok, detail=detail)


# Kontrol türü adı -> fonksiyon eşlemesi. Yeni kontrol eklerken buraya kaydet.
CHECKS = {
    "ping": ping_check,
    # "port": port_check,   # ileride eklenecek
    # "snmp": snmp_check,   # ileride eklenecek
}
