# utils/notificaciones.py
import smtplib
from email.message import EmailMessage

def send_email(to_address, subject, body):
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = "tucorreo@example.com"
    msg["To"] = to_address
    msg.set_content(body)
    # Datos del servidor SMTP (ejemplo con Gmail)
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login("tucorreo@example.com", "tu_contraseña")
        server.send_message(msg)
        server.quit()
    except Exception as e:
        print("Error enviando correo:", e)
