@echo off
cd /d "%~dp0"

IF NOT EXIST "venv" (
    echo Creando entorno virtual...
    python -m venv venv
)

echo Activando entorno virtual e instalando dependencias (esto puede tomar un momento la primera vez)...
call venv\Scripts\activate
pip install -q -r requirements.txt

echo Iniciando SFPoint...
start /b pythonw main.py
