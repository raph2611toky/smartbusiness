from twilio.rest import Client
import os
from dotenv import load_dotenv

load_dotenv()

def send_sms(message="", number_destination=os.getenv('DEFAULT_PHONE_NUMBER')):
    try:
        account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        from_number = os.getenv('TWILIO_NUMBER')
        client = Client(account_sid, auth_token)
        message = client.messages.create(
            from_='+18632655114',
            body=message,
            to=from_number
            )
        print(message.account_sid, message.sid, message.status, message.error_code, message.error_message, message.body)
        print("sms is sended successfully.....")
        return True
    except Exception as e:
        print(e)
        return False

# send_sms(f'Conseil du jour: Votre cycle menstruelle a bien été enregistré. On vous conseil de bien de se preparer si tu envisages une grossesse, c’est le bon moment. Sinon, utilise une protection.')