from apps.users.models import SmsOrangeToken
import os, base64, urllib, json
import http.client

def getAuthToken():
    CLIENT_ID = os.getenv('ORANGE_CLIENT_ID')
    CLIENT_SECRET = os.getenv('ORANGE_CLIENT_SECRET')

    authString = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode('utf-8')
    authorization_basic = os.getenv('ORANGE_AUTHORIZATION_BASIC')

    params = urllib.parse.urlencode({
        "grant_type": "client_credentials"
    })

    headersMap = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": "Basic " + authString
    }

    conn = http.client.HTTPSConnection("api.orange.com")
    conn.request("POST", "/oauth/v3/token", body=params, headers=headersMap)

    response = conn.getresponse()
    
    if response.status == 200:
        data = response.read()
        result = json.loads(data)
        sms_tokens = SmsOrangeToken.objects.all()
        if len(sms_tokens)>0:
            sms_token_last = sms_tokens.last()
            sms_token_last.token_access = result.get('access_token')
            sms_token_last.token_type = result.get('token_type')
            sms_token_last.token_validity = result.get('expires_in')
            sms_token_last.save()
        else:
            SmsOrangeToken.objects.create(token_access=result.get('access_token'), token_type=result.get('token_type'),token_validity=result.get('expires_in'))
        return result
    else:
        print("Error:", response.status, response.reason)
        data = response.read()
        print("Response:", data)
        raise Exception(data)
    conn.close()
    return None

def getOrangeToken():
    sms_tokens = SmsOrangeToken.objects.all()
    if len(sms_tokens)==0:
        auth_token = getAuthToken()
        if auth_token is None:
            raise Exception('Pas de token disponible')
        return auth_token.get('access_token')
    return sms_tokens.last().token_access

def send_sms(recipient_phone, message):
    try:
        # print(f'sending message : {message}  To {recipient_phone}')
        dev_phone = os.getenv('ORANGE_DEV_PHONE_NUMBER')
        token = getAuthToken().get('access_token')

        url = f"/smsmessaging/v1/outbound/tel%3A%2B{dev_phone}/requests"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }

        body = json.dumps({
            "outboundSMSMessageRequest": {
                "address": f"tel:{recipient_phone}",
                "senderAddress": f"tel:+{dev_phone}",
                "outboundSMSTextMessage": {
                    "message": message
                }
            }
        })

        conn = http.client.HTTPSConnection("api.orange.com")
        conn.request("POST", url, body=body, headers=headers)

        response = conn.getresponse()
        data = response.read()
        conn.close()
        print("================== CONSOLE LOG ====================")
        print(json.loads(data), response.reason, response.status)
        if response.status==201:
            print('✅ Message envoyé avec succès...')
        print("================== CONSOLE LOG ====================")
        return json.loads(data) if response.status == 201 else {"error": response.status, "message": response.reason}
    except Exception as e:
        print('imposible d\'envoyer le sms',e)
        return {}

def sms_balance():
    token = token = getOrangeToken()
    url = f"/sms/admin/v1/contracts"

    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    conn = http.client.HTTPSConnection("api.orange.com")
    print('before posting....')
    conn.request("GET", url, headers=headers)

    response = conn.getresponse()
    data = response.read()
    conn.close()

    return json.loads(data) if response.status == 200 else {"error": response.status, "message": response.reason}

def sms_usage():
    token = token = getOrangeToken()

    url = f"/sms/admin/v1/statistics"

    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    conn = http.client.HTTPSConnection("api.orange.com")
    print('before posting....')
    conn.request("GET", url, headers=headers)

    response = conn.getresponse()
    data = response.read()
    conn.close()

    return json.loads(data) if response.status == 200 else {"error": response.status, "message": response.reason}

def sms_purchase_history():
    token = token = getOrangeToken()

    url = f"/sms/admin/v1/purchaseorders"

    headers = {
        "Content-Type":"application/json",
        "Authorization": f"Bearer {token}"
    }
    
    conn = http.client.HTTPSConnection("api.orange.com")
    conn.request("GET", url, headers=headers)

    response = conn.getresponse()
    data = response.read()
    conn.close()

    return json.loads(data) if response.status == 200 else {"error": response.status, "message": response.reason}
