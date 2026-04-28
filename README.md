# 🔔 Price Monitor — Monitor de Preços

Monitor automático de preços para anúncios portugueses.  
Define um preço objetivo e recebe alertas por **email e Telegram** assim que o preço baixar.

---

## ✨ Funcionalidades

- 🔍 Scraping automático de preços (4 sites suportados)
- 💾 Histórico de preços em base de dados SQLite
- 📧 Alertas por email quando o preço atinge o objetivo
- 📱 Notificações por Telegram em tempo real
- 📊 Dashboard web com gráficos de histórico
- ✏️ Adicionar, editar e apagar produtos
- ⏰ Agendamento automático no Windows (Task Scheduler)
- 🔁 Loop contínuo configurável

---

## 🌐 Sites Suportados

| Site | Domínio |
|------|---------|
| StandVirtual | standvirtual.com |
| CustoJusto | custojusto.pt |
| Imovirtual | imovirtual.com |
| AutoSapo | autosapo.pt |

---

## 🚀 Instalação

```bash
git clone https://github.com/Daniel280306/Daniel280306-price_monitor
cd Daniel280306-price_monitor
py -m pip install -r requirements.txt
```

### Configurar `src/config.py`

```python
# Email (Gmail App Password)
EMAIL_SENDER   = "o_teu_email@gmail.com"
EMAIL_PASSWORD = "app_password_16_chars"
EMAIL_RECEIVER = "o_teu_email@gmail.com"

# Telegram
TELEGRAM_TOKEN   = "token_do_botfather"
TELEGRAM_CHAT_ID = "o_teu_chat_id"
SEND_TELEGRAM_ALERTS = True
```

---

## 📖 Uso — Terminal

```bash
py monitor.py add       # Adiciona um produto
py monitor.py check     # Verifica preços agora
py monitor.py run       # Loop contínuo (verifica a cada hora)
py monitor.py list      # Lista produtos monitorizados
py monitor.py history   # Histórico de preços
py monitor.py telegram  # Testa notificação Telegram
```

## 🖥️ Uso — Dashboard Web

```bash
py dashboard.py
# Acede em http://localhost:5000
```

## ⏰ Agendamento Automático Windows

Clica com o botão direito em `schedule_setup.bat` → **Executar como administrador**

---

## 🗂️ Estrutura do Projeto

```
price-monitor/
├── monitor.py              # CLI — ponto de entrada
├── dashboard.py            # Dashboard web Flask
├── schedule_setup.bat      # Ativa agendamento Windows
├── schedule_remove.bat     # Remove agendamento Windows
├── requirements.txt
├── src/
│   ├── config.py           # Configurações (não incluído no git)
│   ├── config.example.py   # Exemplo de configuração
│   ├── database.py         # Base de dados SQLite
│   ├── scraper.py          # Scraping de preços
│   ├── notifier.py         # Alertas por email
│   └── telegram_notifier.py # Alertas por Telegram
├── templates/              # HTML para o dashboard
│   ├── base.html
│   ├── index.html
│   ├── product.html
│   ├── add.html
│   └── edit.html
├── data/                   # Base de dados (gerada automaticamente)
└── logs/                   # Logs de execução
```

---

## 🛠️ Stack

- **Python 3.10+**
- **Flask** — dashboard web
- **BeautifulSoup4** — parsing HTML
- **Requests** — HTTP requests
- **SQLite** — base de dados local
- **smtplib** — alertas por email
- **Telegram Bot API** — notificações mobile

---

## 👤 Autor

**Daniel Santos** — [github.com/Daniel280306](https://github.com/Daniel280306)  
Portfolio: [daniel280306.github.io](https://daniel280306.github.io)
