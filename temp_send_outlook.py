#!/usr/bin/env python3
import requests
import json
import sys

def get_access_token():
    """Get access token for Microsoft Graph API"""
    tenant_id = "f3f1de48-2393-431e-a506-bd5008c40298"
    client_id = "846b39a9-c440-4468-9bae-51e2774a914b"
    
    # Try to get client secret from environment or secrets
    import os
    client_secret = os.getenv('MS_GRAPH_CLIENT_SECRET')
    
    if not client_secret:
        print("Error: MS_GRAPH_CLIENT_SECRET not set")
        return None
    
    url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    
    data = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
        'scope': 'https://graph.microsoft.com/.default'
    }
    
    response = requests.post(url, data=data)
    if response.status_code == 200:
        return response.json().get('access_token')
    else:
        print(f"Token error: {response.status_code} {response.text}")
        return None

def send_email(to_email, subject, body):
    """Send email via Microsoft Graph API"""
    token = get_access_token()
    if not token:
        return False
    
    url = "https://graph.microsoft.com/v1.0/users/Yoni@grit-mind.com/sendMail"
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    message = {
        "message": {
            "subject": subject,
            "body": {
                "contentType": "Text",
                "content": body
            },
            "toRecipients": [
                {
                    "emailAddress": {
                        "address": to_email
                    }
                }
            ]
        }
    }
    
    response = requests.post(url, headers=headers, data=json.dumps(message))
    return response.status_code == 202

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python3 temp_send_outlook.py <to_email> <subject> <body_file>")
        sys.exit(1)
    
    to_email = sys.argv[1]
    subject = sys.argv[2]
    body_file = sys.argv[3]
    
    with open(body_file, 'r', encoding='utf-8') as f:
        body = f.read()
    
    if send_email(to_email, subject, body):
        print("Email sent successfully")
    else:
        print("Failed to send email")