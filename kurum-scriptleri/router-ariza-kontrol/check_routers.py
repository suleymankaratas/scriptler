"""Router arıza kontrolünü komut satırından çalıştırır.

Kullanım:
    python check_routers.py
"""

from runner import run_all_checks, setup_logging


def main() -> None:
    setup_logging()
    results = run_all_checks()
    failures = [r for r in results if not r["ok"]]
    print(f"\nToplam {len(results)} kontrol yapıldı, {len(failures)} arıza bulundu.")


if __name__ == "__main__":
    main()
