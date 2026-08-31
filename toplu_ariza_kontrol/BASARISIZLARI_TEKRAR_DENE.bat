@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ===============================================
echo  DAHA ONCE BASARISIZ OLAN SATIRLAR TEKRAR DENENIYOR
echo  (Excel dosyasinin KAPALI oldugundan emin olun)
echo ===============================================
echo.
python ariza_kontrol.py --retry-failed
echo.
echo ===============================================
echo  TAMAMLANDI. Bu pencereyi kapatabilirsiniz.
echo ===============================================
pause
