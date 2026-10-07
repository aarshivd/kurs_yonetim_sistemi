import os
import requests
import logging

logger = logging.getLogger(__name__)

def send_whatsapp_message(to_number, text):
    """
    Meta WhatsApp Cloud API kullanarak mesaj gönderir.
    to_number: Ülke koduyla numara (örn: '905317725144' veya Cloud API test noları için '905317725144')
    """
    token = os.getenv('WA_ACCESS_TOKEN')
    phone_number_id = os.getenv('WA_PHONE_NUMBER_ID')
    
    if not token or not phone_number_id:
        logger.error("Missing WhatsApp API credentials in .env")
        return False
        
    url = f"https://graph.facebook.com/v19.0/{phone_number_id}/messages"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    data = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to_number,
        "type": "text",
        "text": {
            "preview_url": False,
            "body": text
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        logger.info(f"WhatsApp message sent to {to_number}")
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send WhatsApp message: {str(e)}")
        if e.response is not None:
            logger.error(f"Response: {e.response.text}")
        return None
