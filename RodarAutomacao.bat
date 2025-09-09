@echo off
echo Iniciando automacao...
cd /d "%~dp0"

REM Verificar se existe .venv
if not exist ".venv" (
    echo Erro: Ambiente virtual nao encontrado!
    pause
    exit /b 1
)

REM Executar com Python do venv
.venv\Scripts\python.exe runner.py

REM Log do resultado
if %ERRORLEVEL% EQU 0 (
    echo Automacao concluida com sucesso!
) else (
    echo Erro na execucao! Codigo: %ERRORLEVEL%
)