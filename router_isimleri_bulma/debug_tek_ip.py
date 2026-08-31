import sys
from router_isimleri_bul import MiniTelnet

ip = sys.argv[1] if len(sys.argv) > 1 else "172.22.65.7"
username = sys.argv[2] if len(sys.argv) > 2 else "suleyman.karatas@default"
password = sys.argv[3] if len(sys.argv) > 3 else "Skrts123"
port = int(sys.argv[4]) if len(sys.argv) > 4 else 23

tn = MiniTelnet(ip, port, timeout=8)
banner = tn.read_until(["username:", "login:", "password:", ">", "#"], timeout=8)
print("=== ILK BANNER ===")
print(repr(banner))
print("------------------")
print(banner)

if "username" in banner.lower() or "login" in banner.lower():
    tn.write(username)
    banner = tn.read_until(["password:", ">", "#"], timeout=8)
    print("=== KULLANICI ADI SONRASI ===")
    print(repr(banner))
    print(banner)

if "password" in banner.lower():
    tn.write(password)
    banner = tn.read_until([">", "#", "denied", "incorrect", "failed", "invalid"], timeout=8)
    print("=== SIFRE SONRASI ===")
    print(repr(banner))
    print(banner)

tn.close()
