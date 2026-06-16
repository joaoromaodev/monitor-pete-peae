@echo off
REM Monitor PETE/PEAE - lancador (porta 8531, ao lado do Diarias 8501)
cd /d "%~dp0"

REM se o servidor ja estiver no ar, apenas abre o navegador
powershell -NoProfile -Command "if (Get-NetTCPConnection -LocalPort 8531 -State Listen -ErrorAction SilentlyContinue) { Start-Process 'http://localhost:8531'; exit 0 } else { exit 1 }"
if %errorlevel%==0 exit /b

REM senao, inicia o servidor (o Streamlit abre o navegador sozinho)
python -m streamlit run app.py --server.port 8531
