@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ===============================================
echo  ARIZA KONTROL BASLIYOR
echo  (Excel dosyasinin KAPALI oldugundan emin olun)
echo ===============================================
echo.
python ariza_kontrol.py
echo.
echo ===============================================
echo  TAMAMLANDI. Bu pencereyi kapatabilirsiniz.
echo ===============================================
pause
