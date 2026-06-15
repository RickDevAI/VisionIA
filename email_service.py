"""
email_service.py — Serviço de envio de e-mail via Gmail SMTP.
Usado para: convites de acesso e recuperação de senha.
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

GMAIL_USER     = os.getenv("GMAIL_USER", "")
GMAIL_PASSWORD = os.getenv("GMAIL_PASSWORD", "")
APP_URL        = os.getenv("APP_URL", "https://vision-ia-sandy.vercel.app")


def _enviar(destinatario: str, assunto: str, html: str):
    """Envia um e-mail HTML via Gmail SMTP."""
    if not GMAIL_USER or not GMAIL_PASSWORD:
        raise RuntimeError("Variáveis GMAIL_USER e GMAIL_PASSWORD não configuradas.")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = assunto
    msg["From"]    = f"VisionIA <{GMAIL_USER}>"
    msg["To"]      = destinatario

    msg.attach(MIMEText(html, "html", "utf-8"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(GMAIL_USER, GMAIL_PASSWORD)
        smtp.sendmail(GMAIL_USER, destinatario, msg.as_string())


def enviar_convite(destinatario: str, token: str, convidado_por: str):
    """Envia e-mail de convite para acesso ao VisionIA."""
    link = f"{APP_URL}/cadastro?convite={token}"
    html = f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head><meta charset="UTF-8"></head>
    <body style="margin:0;padding:0;background:#f4f6f9;font-family:Arial,sans-serif;">
      <table width="100%" cellpadding="0" cellspacing="0">
        <tr><td align="center" style="padding:40px 20px;">
          <table width="560" cellpadding="0" cellspacing="0" style="background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08);">

            <!-- Header -->
            <tr><td style="background:#0f2744;padding:28px 40px;text-align:center;">
              <h1 style="color:#fff;margin:0;font-size:24px;letter-spacing:1px;">VisionIA</h1>
              <p style="color:#94a3b8;margin:4px 0 0;font-size:13px;">Validação de Screenshots GMS com IA</p>
            </td></tr>

            <!-- Corpo -->
            <tr><td style="padding:36px 40px;">
              <h2 style="color:#0f2744;margin:0 0 12px;font-size:20px;">Você foi convidado!</h2>
              <p style="color:#475569;font-size:14px;line-height:1.7;margin:0 0 24px;">
                <strong>{convidado_por}</strong> convidou você para acessar o <strong>VisionIA</strong>,
                a plataforma de validação inteligente de screenshots GMS.
              </p>
              <p style="color:#475569;font-size:14px;line-height:1.7;margin:0 0 28px;">
                Clique no botão abaixo para criar sua conta. Este convite é válido por <strong>24 horas</strong>.
              </p>

              <!-- Botão -->
              <table cellpadding="0" cellspacing="0" style="margin:0 auto 28px;">
                <tr><td style="background:#22c55e;border-radius:8px;padding:14px 32px;text-align:center;">
                  <a href="{link}" style="color:#fff;text-decoration:none;font-weight:700;font-size:15px;">
                    Aceitar convite e criar conta
                  </a>
                </td></tr>
              </table>

              <p style="color:#94a3b8;font-size:12px;text-align:center;margin:0;">
                Se o botão não funcionar, copie e cole este link no navegador:<br>
                <a href="{link}" style="color:#0f2744;word-break:break-all;">{link}</a>
              </p>
            </td></tr>

            <!-- Footer -->
            <tr><td style="background:#f8fafc;padding:20px 40px;text-align:center;border-top:1px solid #e2e8f0;">
              <p style="color:#94a3b8;font-size:11px;margin:0;">
                Se você não esperava este convite, pode ignorar este e-mail.<br>
                © 2025 VisionIA — Fametro · Sistemas da Informação
              </p>
            </td></tr>

          </table>
        </td></tr>
      </table>
    </body>
    </html>
    """
    _enviar(destinatario, "Convite para o VisionIA 🎉", html)


def enviar_recuperacao_senha(destinatario: str, token: str, nome: str):
    """Envia e-mail de recuperação de senha."""
    link = f"{APP_URL}/redefinir-senha?token={token}"
    html = f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head><meta charset="UTF-8"></head>
    <body style="margin:0;padding:0;background:#f4f6f9;font-family:Arial,sans-serif;">
      <table width="100%" cellpadding="0" cellspacing="0">
        <tr><td align="center" style="padding:40px 20px;">
          <table width="560" cellpadding="0" cellspacing="0" style="background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08);">

            <!-- Header -->
            <tr><td style="background:#0f2744;padding:28px 40px;text-align:center;">
              <h1 style="color:#fff;margin:0;font-size:24px;letter-spacing:1px;">VisionIA</h1>
              <p style="color:#94a3b8;margin:4px 0 0;font-size:13px;">Validação de Screenshots GMS com IA</p>
            </td></tr>

            <!-- Corpo -->
            <tr><td style="padding:36px 40px;">
              <h2 style="color:#0f2744;margin:0 0 12px;font-size:20px;">Redefinir senha</h2>
              <p style="color:#475569;font-size:14px;line-height:1.7;margin:0 0 24px;">
                Olá, <strong>{nome}</strong>! Recebemos uma solicitação para redefinir a senha da sua conta VisionIA.
              </p>
              <p style="color:#475569;font-size:14px;line-height:1.7;margin:0 0 28px;">
                Clique no botão abaixo para criar uma nova senha. Este link é válido por <strong>1 hora</strong>.
              </p>

              <!-- Botão -->
              <table cellpadding="0" cellspacing="0" style="margin:0 auto 28px;">
                <tr><td style="background:#0f2744;border-radius:8px;padding:14px 32px;text-align:center;">
                  <a href="{link}" style="color:#fff;text-decoration:none;font-weight:700;font-size:15px;">
                    Redefinir minha senha
                  </a>
                </td></tr>
              </table>

              <p style="color:#94a3b8;font-size:12px;text-align:center;margin:0 0 16px;">
                Se o botão não funcionar, copie e cole este link no navegador:<br>
                <a href="{link}" style="color:#0f2744;word-break:break-all;">{link}</a>
              </p>

              <p style="color:#ef4444;font-size:12px;text-align:center;margin:0;">
                Se você não solicitou a redefinição de senha, ignore este e-mail.<br>
                Sua senha permanece a mesma.
              </p>
            </td></tr>

            <!-- Footer -->
            <tr><td style="background:#f8fafc;padding:20px 40px;text-align:center;border-top:1px solid #e2e8f0;">
              <p style="color:#94a3b8;font-size:11px;margin:0;">
                © 2025 VisionIA — Fametro · Sistemas da Informação
              </p>
            </td></tr>

          </table>
        </td></tr>
      </table>
    </body>
    </html>
    """
    _enviar(destinatario, "Redefinição de senha — VisionIA 🔐", html)
