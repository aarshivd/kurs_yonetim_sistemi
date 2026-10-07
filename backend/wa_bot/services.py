from .models import WhatsAppMessageLog
from .utils import send_whatsapp_message as meta_send_message
import logging

logger = logging.getLogger(__name__)

def send_whatsapp_message(phone_number: str, text: str, recipient=None, message_type='OTHER'):
    """
    Sinyallerin veya view'ların doğrudan kullandığı, loglama ve hata yakalama
    işlemlerini saran (wrapper) servis fonksiyonu.
    """
    try:
        response = meta_send_message(phone_number, text)
        if response:
            WhatsAppMessageLog.objects.create(
                recipient=recipient,
                phone_number=phone_number,
                direction='OUT',
                message_type=message_type,
                content=text
            )
            return True
        else:
            WhatsAppMessageLog.objects.create(
                recipient=recipient, 
                phone_number=phone_number,
                direction='OUT', 
                message_type=message_type, 
                content=f"[HATA] {text}"
            )
            return False
    except Exception as e:
        logger.error(f"Error in send_whatsapp_message wrapper: {e}")
        WhatsAppMessageLog.objects.create(
            recipient=recipient,
            phone_number=phone_number,
            direction='OUT',
            message_type=message_type,
            content=f"[HATA: {e}] {text}"
        )
        return False
