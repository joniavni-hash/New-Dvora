#!/usr/bin/env python3
"""
Email Review Script - Fetch and categorize emails for daily review
"""
import requests
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Microsoft Graph API configuration
TENANT_ID = "f3f1de48-2393-431e-a506-bd5008c40298"
CLIENT_ID = "846b39a9-c440-4468-9bae-51e2774a914b"
USER_EMAIL = "Yoni@grit-mind.com"

def get_access_token():
    """Get access token for Microsoft Graph API"""
    # Try multiple sources for credentials
    tenant_id = TENANT_ID
    client_id = CLIENT_ID
    client_secret = None
    
    # Method 1: Environment variables
    client_secret = os.getenv('MS_GRAPH_CLIENT_SECRET')
    
    # Method 2: OpenClaw root .env file
    if not client_secret:
        openclaw_env = Path("/home/ubuntu/.openclaw/.env")
        if openclaw_env.exists():
            for line in openclaw_env.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    if k.strip() == 'MS_GRAPH_CLIENT_SECRET':
                        client_secret = v.strip()
                        break

    # Method 3: /home/ubuntu/.openclaw/.env file
    if not client_secret:
        secrets_file = Path("/home/ubuntu/.openclaw/.env")
        if secrets_file.exists():
            for line in secrets_file.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    if k.strip() == 'MS_GRAPH_CLIENT_SECRET':
                        client_secret = v.strip()
                        break

    # Method 4: Use temp_send_outlook.py method
    if not client_secret:
        try:
            sys.path.append(str(Path(__file__).parent.parent))
            import temp_send_outlook
            # Try to get token from temp script
            temp_token = temp_send_outlook.get_access_token()
            if temp_token:
                return temp_token, None
        except:
            pass
    
    if not client_secret:
        return None, "MS_GRAPH_CLIENT_SECRET not found in environment, /home/ubuntu/.openclaw/.env, or temp script"
    
    url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
    
    data = {
        'grant_type': 'client_credentials',
        'client_id': CLIENT_ID,
        'client_secret': client_secret,
        'scope': 'https://graph.microsoft.com/.default'
    }
    
    try:
        response = requests.post(url, data=data, timeout=10)
        if response.status_code == 200:
            return response.json().get('access_token'), None
        else:
            # Parse Azure error for actionable diagnostics
            error_detail = ""
            try:
                err = response.json()
                azure_error = err.get('error', '')
                azure_desc = err.get('error_description', '')
                if 'invalid_client' in azure_error or 'invalid_client' in azure_desc:
                    error_detail = "SECRET_EXPIRED: ה-secret של Outlook פג תוקף ב-Azure. צריך ליצור secret חדש ב-Azure Portal ולעדכן ב-/home/ubuntu/.openclaw/.env"
                elif 'unauthorized_client' in azure_error:
                    error_detail = "PERMISSIONS: ל-client אין הרשאות מתאימות ב-Azure. צריך לבדוק App Registration permissions."
                else:
                    error_detail = f"AZURE_ERROR: {azure_error} — {azure_desc[:200]}"
            except:
                error_detail = f"HTTP {response.status_code}"
            return None, error_detail
    except requests.exceptions.Timeout:
        return None, "TIMEOUT: Graph API לא מגיב. כנראה בעיית רשת."
    except requests.exceptions.ConnectionError:
        return None, "CONNECTION_ERROR: לא ניתן להתחבר ל-Azure. בדקי חיבור רשת."
    except Exception as e:
        return None, f"REQUEST_ERROR: {e}"

def fetch_emails(token, days=2):
    """Fetch emails from the last N days"""
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # Calculate date filter
    since_date = (datetime.now() - timedelta(days=days)).isoformat() + 'Z'
    
    # Get messages with basic info
    url = f"https://graph.microsoft.com/v1.0/users/{USER_EMAIL}/messages"
    params = {
        '$filter': f"receivedDateTime ge {since_date}",
        '$select': 'id,subject,sender,receivedDateTime,isRead,importance,hasAttachments,bodyPreview',
        '$orderby': 'receivedDateTime desc',
        '$top': 50
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        if response.status_code == 200:
            return response.json().get('value', []), None
        else:
            return [], f"Fetch failed: {response.status_code} - {response.text}"
    except Exception as e:
        return [], f"Request failed: {e}"

def is_spam_or_newsletter(email):
    """Simple spam/newsletter detection"""
    sender_email = email.get('sender', {}).get('emailAddress', {}).get('address', '').lower()
    subject = (email.get('subject') or '').lower()
    
    # Common newsletter/spam patterns
    spam_domains = [
        'noreply', 'no-reply', 'newsletter', 'marketing', 'notifications',
        'updates', 'support', 'hello@', 'info@', 'news@'
    ]
    
    spam_subjects = [
        'unsubscribe', 'newsletter', 'weekly digest', 'daily summary',
        'notification', 'security alert', 'your account', 'verify'
    ]
    
    # Check sender
    for pattern in spam_domains:
        if pattern in sender_email:
            return True
    
    # Check subject
    for pattern in spam_subjects:
        if pattern in subject:
            return True
    
    return False

def format_email_for_review(emails):
    """Format emails for review with numbering and basic info"""
    if not emails:
        return "📧 אין מיילים חדשים מ-48 השעות האחרונות"
    
    # Filter out spam/newsletters
    important_emails = [e for e in emails if not is_spam_or_newsletter(e)]
    
    if not important_emails:
        return f"📧 נבדקו {len(emails)} מיילים - כולם ניוזלטרים/ספאם, אין מה לסווג"
    
    review_text = "📧 סקירת מיילים - 48 שעות אחרונות\n\n"
    
    for i, email in enumerate(important_emails[:10], 1):  # Max 10 emails
        sender = email.get('sender', {}).get('emailAddress', {})
        sender_name = sender.get('name', sender.get('address', 'לא ידוע'))
        subject = email.get('subject', 'ללא נושא')
        received = email.get('receivedDateTime', '')
        is_read = '✅' if email.get('isRead') else '🔴'
        has_attachments = '📎' if email.get('hasAttachments') else ''
        
        # Parse date for display
        try:
            date_obj = datetime.fromisoformat(received.replace('Z', '+00:00'))
            date_str = date_obj.strftime('%d.%m %H:%M')
        except:
            date_str = received[:16] if received else ''
        
        review_text += f"{i}️⃣ {sender_name} — {subject} {has_attachments}\n"
        review_text += f"   📅 {date_str} {is_read}\n\n"
    
    if len(important_emails) > 10:
        review_text += f"... ועוד {len(important_emails) - 10} מיילים\n\n"
    
    review_text += "סווג: 🔴 מיידי 🟡 חשוב לא מיידי ⚪ לא חשוב\n"
    review_text += f"📊 סה\"כ: {len(emails)} מיילים, {len(important_emails)} רלוונטיים"
    
    return review_text

# Exit codes:
# 0 = success
# 1 = general error
# 2 = auth failed (secret missing or invalid)
# 3 = API error (authenticated but fetch failed)

def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ['--review', '--test']:
        print("Usage: python3 email_review.py --review [--days N]")
        print("       python3 email_review.py --test")
        return

    days = 2
    if '--days' in sys.argv:
        try:
            days_idx = sys.argv.index('--days') + 1
            days = int(sys.argv[days_idx])
        except:
            days = 2

    if sys.argv[1] == '--test':
        print("Testing Microsoft Graph API connection...")
        token, error = get_access_token()
        if token:
            print("✅ Authentication successful")
            emails, fetch_error = fetch_emails(token, days=1)
            if emails is not None:
                print(f"✅ Email fetch successful - found {len(emails)} emails")
            else:
                print(f"❌ Email fetch failed: {fetch_error}")
                sys.exit(3)
        else:
            print(f"❌ Authentication failed: {error}")
            sys.exit(2)
        return

    # Get access token with retry
    import time
    print("🔐 Authenticating with Microsoft Graph...")
    token, auth_error = get_access_token()
    if not token:
        print(f"⚠️ First attempt failed: {auth_error}")
        print("🔄 Retrying in 3 seconds...")
        time.sleep(3)
        token, auth_error = get_access_token()

    if not token:
        print(f"❌ Authentication failed after 2 attempts: {auth_error}")
        sys.exit(2)

    # Fetch emails
    print(f"📬 Fetching emails from last {days} days...")
    emails, fetch_error = fetch_emails(token, days)
    if emails is None:
        print(f"❌ Failed to fetch emails: {fetch_error}")
        sys.exit(3)

    # Format for review
    review_text = format_email_for_review(emails)
    print(review_text)

if __name__ == "__main__":
    main()