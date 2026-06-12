import requests
from django.core.mail.backends.base import BaseEmailBackend
from django.conf import settings

class ResendEmailBackend(BaseEmailBackend):
    """
    Backend de correo personalizado para evadir bloqueos de puertos SMTP de Render.
    Envía los correos de Django directamente por la API HTTPS de Resend.
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
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        for message in email_messages:
            # Resend en su modo gratuito (Onboarding) permite enviar correos a ti mismo
            # usando el remitente por defecto: onboarding@resend.dev
            payload = {
                "from": "onboarding@resend.dev",
                "to": message.to,
                "subject": message.subject,
                "text": message.body,
            }
            
            try:
                # La petición se hace mediante HTTPS (puerto 443), por lo que no se bloquea en Render
                response = requests.post(
                    "https://api.resend.com/emails",
                    json=payload,
                    headers=headers,
                    timeout=10
                )
                if response.status_code in [200, 201]:
                    sent_count += 1
            except Exception:
                pass
        
        return sent_count