"""
config.py — Configurações do Price Monitor
Edita este ficheiro com os teus dados antes de correr o programa.
"""

# ─── EMAIL ────────────────────────────────────────────────────────────────────
# Usa uma conta Gmail. Para a password, gera uma "App Password":
# Google Account → Segurança → Verificação em 2 etapas → App Passwords
EMAIL_SENDER   = "your_email@gmail.com"
EMAIL_PASSWORD = "your_app_password" # NÃO uses a password normal do Gmail!
EMAIL_RECEIVER = "your_email@gmail.com"     # Para onde enviar os alertas

# ─── COMPORTAMENTO ────────────────────────────────────────────────────────────
# Intervalo entre verificações (em segundos)
# 3600 = 1 hora | 21600 = 6 horas | 86400 = 1 dia
CHECK_INTERVAL = 3600

# Enviar resumo diário? (True/False)
SEND_DAILY_SUMMARY = True
