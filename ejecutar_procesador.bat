@echo off
chcp 65001 > nul
echo =========================================
echo    PROCESADOR AUTOMATICO DE NOMINAS
echo =========================================
echo.

cd /d "%~dp0"

echo ¿Deseas ejecutar el procesador de nominas? (S/N)
set /p respuesta=

if /i "%respuesta%"=="S" (
    echo.
    echo Ejecutando procesador...
    .\.venv\Scripts\python.exe main.py
    echo.
    echo Revisa los mensajes anteriores para ver los resultados
) else (
    echo Ejecucion cancelada.
)

echo.
echo Presiona cualquier tecla para cerrar...
pause >nul
