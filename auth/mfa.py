import smtplib
import email.message
import pyotp
from dotenv import load_dotenv
import os

# Carregar variáveis de ambiente
load_dotenv()

MFA_KEY = os.getenv('MFA_KEY')
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")

def gerar_mfa():
    try:
        if not MFA_KEY:
            raise ValueError("⚠️ Chave-Mestra não configurada corretamente.")
        otp = pyotp.TOTP(MFA_KEY).now()
        return otp
    except Exception as e:
        print(f"❌ Erro ao gerar código: {e}")

def enviar_email(destinatario, otp):
    try:
        if not MFA_KEY or not EMAIL_ADDRESS or not EMAIL_PASSWORD:
            raise ValueError("⚠️ Variáveis de ambiente não configuradas corretamente.")

        if not destinatario:
            raise ValueError("⚠️ Destinatário vázio!")
        if not otp:
            raise ValueError("⚠️ Código vázio!")

        corpo_email = f'''
        <p>Olá, tudo bem?</p>
        <p>Seu código de autenticação é: <strong>{otp}</strong></p>
        <p>Ele expira em 30 segundos.</p>
        '''

        msg = email.message.EmailMessage()
        msg['Subject'] = 'Autenticação de Multi Fatores - Cyber'
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = destinatario
        msg.set_content(corpo_email, subtype='html')

        with smtplib.SMTP('smtp.gmail.com', 587) as s:
            s.starttls()
            s.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            s.sendmail(EMAIL_ADDRESS, msg["To"], msg.as_string())

        print(f"✅ Código enviado para {destinatario}")

    except Exception as e:
        print(f"❌ Erro ao enviar e-mail: {e}")