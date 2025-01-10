import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import settings  # Asegúrate de que `config.py` esté correctamente configurado

# Crear el mensaje
subject = "Prueba de envío de correo"
body = "Este es un correo de prueba enviado usando SMTP en Python."

msg = MIMEMultipart()
msg["From"] = f"{settings.MAIL_FROM_NAME} <{settings.MAIL_FROM_EMAIL}>"
msg["To"] = "luis3.14xbox@gmail.com" 
msg["Subject"] = subject
msg.attach(MIMEText(body, "plain"))

# Enviar el correo
try:
    with smtplib.SMTP(settings.MAIL_SERVER, settings.MAIL_PORT) as server:
        if settings.MAIL_TLS:
            server.starttls()  # Inicia TLS si está habilitado
        server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
        server.sendmail(settings.MAIL_FROM_EMAIL, "marcosaenz31@hotmail.com", msg.as_string())
        print("Correo enviado con éxito.")
except Exception as e:
    print(f"Error al enviar el correo: {e}")