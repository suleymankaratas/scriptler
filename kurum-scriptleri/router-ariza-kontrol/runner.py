"""Kontrolleri çalıştıran ortak mantık.

Hem CLI script (check_routers.py) hem de arayüz (app.py) buradaki
`run_all_checks()` fonksiyonunu kullanır — mantık tek yerde durur.
"""

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    # Bu modül bir paketin parçası olarak (örn. merkezi workspace menüsünden)
    # yüklendiğinde, isim çakışmasını önlemek için göreli import kullanılır.
    from .checks import CHECKS
    from .config import LOG_PATH, ROUTERS
except ImportError:
    # Tek başına çalıştırıldığında (örn. check_routers.py üzerinden) paket
    # bağlamı olmadığı için düz import'a düşer.
    from checks import CHECKS
    from config import LOG_PATH, ROUTERS


def setup_logging() -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.FileHandler(LOG_PATH, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
        force=True,
    )


def run_all_checks() -> list[dict]:
    """config.ROUTERS içindeki her router için tanımlı kontrolleri çalıştırır.

    Döner: her biri {"name", "ip", "check", "ok", "detail"} içeren bir liste.
    Sonuçlar ayrıca log dosyasına ve konsola yazılır.
    """
    results: list[dict] = []

    for router in ROUTERS:
        name = router["name"]
        ip = router["ip"]
        for check_name in router.get("checks", ["ping"]):
            check_fn = CHECKS.get(check_name)
            if check_fn is None:
                logging.warning("%s (%s): bilinmeyen kontrol turu '%s'", name, ip, check_name)
                continue

            result = check_fn(ip)
            level = logging.INFO if result.ok else logging.ERROR
            status = "OK" if result.ok else "ARIZA"
            logging.log(level, "%s (%s) [%s]: %s - %s", name, ip, check_name, status, result.detail)

            results.append(
                {
                    "name": name,
                    "ip": ip,
                    "check": check_name,
                    "ok": result.ok,
                    "detail": result.detail,
                }
            )

    return results
