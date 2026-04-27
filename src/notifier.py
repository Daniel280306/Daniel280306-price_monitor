"""
notifier.py — Envia alertas por email quando o preço baixa
"""
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from config import EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECEIVER


def send_alert(product_name: str, url: str, current_price: float,
               target_price: float, previous_price: float | None):
    """Envia email de alerta quando o preço atinge o objetivo."""

    subject = f"🔔 Alerta de Preço: {product_name} — {current_price}€"

    # Corpo do email em HTML
    prev_line = (
        f"<li><b>Preço anterior:</b> {previous_price}€</li>"
        if previous_price else ""
    )

    html = f"""
    <html><body style="font-family:Arial,sans-serif;max-width:600px;margin:auto;">
      <div style="background:#1a1a2e;padding:24px;border-radius:8px 8px 0 0;">
        <h2 style="color:#00e5ff;margin:0;">🔔 Alerta de Preço Atingido!</h2>
      </div>
      <div style="background:#f9f9f9;padding:24px;border-radius:0 0 8px 8px;border:1px solid #eee;">
        <h3 style="color:#1a1a2e;">{product_name}</h3>
        <ul style="line-height:2;">
          <li><b>Preço atual:</b> <span style="color:green;font-size:1.2em;"><b>{current_price}€</b></span></li>
          {prev_line}
          <li><b>Teu objetivo:</b> {target_price}€</li>
        </ul>
        <a href="{url}"
           style="display:inline-block;background:#1a1a2e;color:white;
                  padding:12px 24px;border-radius:6px;text-decoration:none;
                  margin-top:12px;">
          Ver Anúncio no OLX →
        </a>
        <p style="color:#999;font-size:12px;margin-top:24px;">
          Enviado pelo Price Monitor · <a href="{url}">{url}</a>
        </p>
      </div>
    </body></html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())
        print(f"[EMAIL] Alerta enviado para {EMAIL_RECEIVER}: {product_name} a {current_price}€")
    except smtplib.SMTPAuthenticationError:
        print("[EMAIL] Erro de autenticação — verifica o EMAIL e APP PASSWORD no config.py")
    except Exception as e:
        print(f"[EMAIL] Erro ao enviar email: {e}")


def send_summary(results: list):
    """Envia um resumo diário de todos os produtos monitorizados."""
    if not results:
        return

    rows = ""
    for r in results:
        color = "green" if r["below_target"] else "#333"
        flag = " 🔔" if r["below_target"] else ""
        rows += f"""
        <tr>
          <td style="padding:8px;border-bottom:1px solid #eee;">{r['name']}{flag}</td>
          <td style="padding:8px;border-bottom:1px solid #eee;color:{color};font-weight:bold;">{r['price']}€</td>
          <td style="padding:8px;border-bottom:1px solid #eee;">{r['target']}€</td>
        </tr>
        """

    html = f"""
    <html><body style="font-family:Arial,sans-serif;max-width:600px;margin:auto;">
      <div style="background:#1a1a2e;padding:24px;border-radius:8px 8px 0 0;">
        <h2 style="color:#00e5ff;margin:0;">📊 Resumo Diário de Preços</h2>
      </div>
      <div style="background:#f9f9f9;padding:24px;border-radius:0 0 8px 8px;border:1px solid #eee;">
        <table style="width:100%;border-collapse:collapse;">
          <thead>
            <tr style="background:#e8f0f5;">
              <th style="padding:8px;text-align:left;">Produto</th>
              <th style="padding:8px;text-align:left;">Preço Atual</th>
              <th style="padding:8px;text-align:left;">Objetivo</th>
            </tr>
          </thead>
          <tbody>{rows}</tbody>
        </table>
      </div>
    </body></html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "📊 Price Monitor — Resumo Diário"
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())
        print(f"[EMAIL] Resumo diário enviado.")
    except Exception as e:
        print(f"[EMAIL] Erro ao enviar resumo: {e}")
