@echo off
echo A remover tarefa agendada PriceMonitor...
schtasks /delete /tn "PriceMonitor" /f
if %errorlevel% == 0 (
    echo [OK] Tarefa removida com sucesso!
) else (
    echo [INFO] Tarefa nao encontrada ou ja removida.
)
pause
