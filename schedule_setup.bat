@echo off
echo ================================================
echo   Price Monitor - Configurar Agendamento Windows
echo ================================================
echo.

:: Obter o caminho absoluto da pasta atual
set "PROJECT_DIR=%~dp0"
set "PROJECT_DIR=%PROJECT_DIR:~0,-1%"

:: Caminho para o Python e script
set "PYTHON=py"
set "SCRIPT=%PROJECT_DIR%\monitor.py"
set "LOG=%PROJECT_DIR%\logs\scheduler.log"

echo Projeto: %PROJECT_DIR%
echo.

:: Criar pasta de logs se nao existir
if not exist "%PROJECT_DIR%\logs" mkdir "%PROJECT_DIR%\logs"

:: Remover tarefa anterior se existir
schtasks /delete /tn "PriceMonitor" /f >nul 2>&1

:: Criar tarefa agendada a cada hora
schtasks /create ^
  /tn "PriceMonitor" ^
  /tr "%PYTHON% \"%SCRIPT%\" check >> \"%LOG%\" 2>&1" ^
  /sc HOURLY ^
  /mo 1 ^
  /st 00:00 ^
  /ru "%USERNAME%" ^
  /f

if %errorlevel% == 0 (
    echo [OK] Tarefa agendada com sucesso!
    echo      O monitor vai verificar precos a cada hora automaticamente.
    echo.
    echo Para verificar: schtasks /query /tn "PriceMonitor"
    echo Para remover:   schtasks /delete /tn "PriceMonitor" /f
    echo Logs em:        %LOG%
) else (
    echo [ERRO] Nao foi possivel criar a tarefa.
    echo        Tenta correr este ficheiro como Administrador.
    echo        Clica com o botao direito -> "Executar como administrador"
)

echo.
pause
