@echo off
cd /d C:\Users\secto\anime_catalogo

echo ==========================
echo VERIFICANDO DJANGO...
echo ==========================

python manage.py check

IF ERRORLEVEL 1 (
    echo.
    echo ERROR EN DJANGO.
    pause
    exit /b
)

echo.
echo ==========================
echo VERIFICANDO FECHA...
echo ==========================

set ACTUALIZAR=0

IF NOT EXIST ultima_actualizacion_animes.txt (
    set ACTUALIZAR=1
)

IF EXIST ultima_actualizacion_animes.txt (
    forfiles /p . /m ultima_actualizacion_animes.txt /d -30 >nul 2>&1
    IF NOT ERRORLEVEL 1 (
        set ACTUALIZAR=1
    )
)

IF "%ACTUALIZAR%"=="1" (
    echo Actualizando animes...
    python manage.py actualizar_animes_emision

    IF ERRORLEVEL 1 (
        echo.
        echo ERROR AL ACTUALIZAR ANIMES.
        pause
        exit /b
    )

    echo actualizado > ultima_actualizacion_animes.txt
) ELSE (
    echo No hace falta actualizar animes todavia.
)

echo.
echo ==========================
echo INICIANDO SERVER...
echo ==========================

python manage.py runserver

pause