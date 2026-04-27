# 🔔 Price Monitor — Monitor de Preços OLX

Monitor automático de preços para anúncios do OLX Portugal.  
Define um preço objetivo e recebe um **email de alerta** assim que o preço baixar.

---

## ✨ Funcionalidades

- 🔍 Scraping automático de preços do OLX
- 💾 Histórico de preços em base de dados SQLite
- 📧 Alertas por email quando o preço atinge o objetivo
- 📊 Resumo diário de todos os produtos monitorizados
- ⏰ Loop automático configurável (ex: verificar a cada hora)

---

## 🚀 Instalação

```bash
# 1. Clona o repositório
git clone https://github.com/Daniel280306/price-monitor
cd price-monitor

# 2. Instala as dependências
pip install -r requirements.txt

# 3. Configura o email
# Edita src/config.py com o teu email e App Password do Gmail
```

### Configurar App Password do Gmail
1. Google Account → Segurança → Verificação em 2 etapas
2. App Passwords → Gera uma password para "Mail"
3. Cola em `src/config.py`

---

## 📖 Uso

```bash
# Adicionar um produto para monitorizar
python monitor.py add

# Verificar preços agora (uma vez)
python monitor.py check

# Correr em loop contínuo (verifica a cada hora)
python monitor.py run

# Ver todos os produtos monitorizados
python monitor.py list

# Ver histórico de preços
python monitor.py history
```

---

## 🗂️ Estrutura do Projeto

```
price-monitor/
├── monitor.py          # Script principal (ponto de entrada)
├── requirements.txt    # Dependências Python
├── src/
│   ├── config.py       # Configurações (email, intervalos)
│   ├── database.py     # Gestão da base de dados SQLite
│   ├── scraper.py      # Scraping de preços do OLX
│   └── notifier.py     # Envio de alertas por email
├── data/
│   └── prices.db       # Base de dados (gerada automaticamente)
└── logs/               # Logs de execução
```

---

## 🛠️ Stack

- **Python 3.10+**
- **BeautifulSoup4** — parsing HTML
- **Requests** — HTTP requests
- **SQLite** — base de dados local
- **smtplib** — envio de emails

---

## 👤 Autor

**Daniel Santos** — [github.com/Daniel280306](https://github.com/Daniel280306)  
Portfolio: [daniel280306.github.io](https://daniel280306.github.io)
