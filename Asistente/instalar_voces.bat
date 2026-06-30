@echo off
echo ================================================
echo   INSTALACION DE VOCES NEURALES PARA FRANK
echo ================================================
echo.

echo [1/2] Activando entorno virtual...
call frank_env\Scripts\activate

echo [2/2] Instalando edge-tts y playsound...
pip install edge-tts playsound

echo.
echo ================================================
echo   Instalacion completada.
echo   Abriendo el probador de voces...
echo ================================================
echo.

python probar_voces.py

pause
