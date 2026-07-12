import requests
from django.core.mail.backends.base import BaseEmailBackend
from django.conf import settings

class BrevoEmailBackend(BaseEmailBackend):
    """
    Backend de correo personalizado para enviar correos usando la API HTTP de Brevo.
    Evita los bloqueos de puertos SMTP en Render y permite usar un remitente de Gmail verificado.
    """
    def send_messages(self, email_messages):
        if not email_messages:
            return 0
        
        # Leemos la API Key de Resend desde la configuración de Django
        api_key = getattr(settings, 'RESEND_API_KEY', None)
        if not api_key:
            return 0
        
        sent_count = 0
        headers = {
            "api-key": api_key,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        for message in email_messages:
            # Resend en su modo gratuito (Onboarding) permite enviar correos a ti mismo
            # usando el remitente por defecto: onboarding@resend.dev
            payload = {
                "sender": {
                    "name": "Ritnova360",
                    "email": "ritnova360@gmail.com"  # Su correo de Gmail ya verificado en Brevo
                },
                "to": [{"email": recipient} for recipient in message.to],
                "subject": message.subject,
                "textContent": message.body,
            }
            
            try:
                # La petición se hace mediante HTTPS (puerto 443), por lo que no se bloquea en Render
                response = requests.post(
                    "https://api.brevo.com/v3/smtp/email",
                    json=payload,
                    headers=headers,
                    timeout=10
                )
                if response.status_code in [200, 201, 202]:
                    sent_count += 1
            except Exception:
                pass
        
        return sent_count