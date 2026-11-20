@echo off
chcp 65001 >nul
cd /d "%~dp0"

if not exist .venv (
    python -m venv .venv
    call .venv\Scripts\activate.bat
    python -m pip install -r requirements.txt
) else (
    call .venv\Scripts\activate.bat
)

pyinstaller --noconfirm --clean --onefile --windowed ^
    --name "ContextBuilderAI" ^
    --icon=icon.ico ^
    --add-data "icon.ico;." ^
    --hidden-import=tiktoken_ext.openai_public ^
    --hidden-import=tiktoken_ext ^
    main.py

echo.
echo Сборка завершена: dist\ContextBuilderAI.exe
pause