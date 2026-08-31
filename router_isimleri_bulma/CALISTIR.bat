@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ===============================================
echo  ROUTER ISIMLERI BULMA BASLIYOR
echo  (Excel dosyasinin KAPALI oldugundan emin olun)
echo ===============================================
echo.
python router_isimleri_bul.py
echo.
echo ===============================================
echo  TAMAMLANDI. Bu pencereyi kapatabilirsiniz.
echo ===============================================
pause
