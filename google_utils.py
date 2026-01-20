import os
import base64
import datetime
from dotenv import load_dotenv
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Load environment (for ZOOM_ROOM_URL)
load_dotenv()
ZOOM_URL = os.getenv("ZOOM_ROOM_URL")

# Unified credentials
SCOPES = [
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/calendar.events',
    "https://www.googleapis.com/auth/calendar.readonly"
]

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_PATH = os.path.join(_SCRIPT_DIR, "memory", "google_credentials.json")
TOKEN_PATH = os.path.join(_SCRIPT_DIR, "memory", "token.json")

def get_google_service(api_name, version):
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=8080)
        with open(TOKEN_PATH, "w") as token:
            token.write(creds.to_json())
    return build(api_name, version, credentials=creds)

# ───── Gmail Functions ─────

def list_emails(query='is:unread', max_results=5):
    service = get_google_service('gmail', 'v1')
    results = service.users().messages().list(userId='me', q=query, maxResults=max_results).execute()
    messages = results.get('messages', [])
    emails = []

    def extract_plain_text(payload):
        if payload.get("mimeType") == "text/plain":
            data = payload.get("body", {}).get("data", "")
            return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
        elif payload.get("mimeType", "").startswith("multipart/"):
            for part in payload.get("parts", []):
                result = extract_plain_text(part)
                if result:
                    return result
        return ""

    for msg in messages:
        msg_data = service.users().messages().get(userId='me', id=msg['id'], format='full').execute()
        payload = msg_data.get('payload', {})
        headers = payload.get('headers', [])
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '(No Subject)')
        sender = next((h['value'] for h in headers if h['name'] == 'From'), '(Unknown Sender)')
        body = extract_plain_text(payload)

        emails.append({
            'id': msg['id'],
            'subject': subject,
            'from': sender,
            'body': body.strip() or '[No body found]',
            'snippet': msg_data.get('snippet', '')
        })

    return emails

def mark_as_read(msg_id):
    service = get_google_service('gmail', 'v1')
    service.users().messages().modify(userId='me', id=msg_id, body={'removeLabelIds': ['UNREAD']}).execute()

def star_email(msg_id):
    service = get_google_service('gmail', 'v1')
    service.users().messages().modify(userId='me', id=msg_id, body={'addLabelIds': ['STARRED']}).execute()

def send_email(to, subject, body_text, cc=None):
    service = get_google_service('gmail', 'v1')
    message = MIMEText(body_text.replace("\\n", "\n"), "plain")

    message['To'] = to if isinstance(to, str) else ", ".join(to)
    if cc:
        message['Cc'] = cc if isinstance(cc, str) else ", ".join(cc)
    message['From'] = "me"
    message['Subject'] = subject

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    service.users().messages().send(userId='me', body={'raw': raw}).execute()

def get_email_by_id(email_id):
    service = get_google_service('gmail', 'v1')
    try:
        msg_data = service.users().messages().get(userId='me', id=email_id, format='full').execute()
        payload = msg_data.get('payload', {})
        headers = payload.get('headers', [])

        def extract_plain_text(payload):
            if payload.get("mimeType") == "text/plain":
                data = payload.get("body", {}).get("data", "")
                return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
            elif payload.get("mimeType", "").startswith("multipart/"):
                for part in payload.get("parts", []):
                    result = extract_plain_text(part)
                    if result:
                        return result
            return ""

        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '(No Subject)')
        sender = next((h['value'] for h in headers if h['name'] == 'From'), '(Unknown Sender)')
        to = next((h['value'] for h in headers if h['name'] == 'To'), '(Unknown Recipient)')
        date = next((h['value'] for h in headers if h['name'] == 'Date'), '(Unknown Date)')
        body = extract_plain_text(payload).strip() or '[No body found]'

        return {
            'id': email_id,
            'subject': subject,
            'from': sender,
            'to': to,
            'date': date,
            'body': body
        }
    except Exception as e:
        print(f"Error fetching email {email_id}: {e}")
        return None

# ───── Calendar Functions ─────

def get_events_between_dates(start_date: str, end_date: str):
    service = get_google_service('calendar', 'v3')

    start_dt = f"{start_date}T00:00:00Z"
    end_dt = f"{end_date}T23:59:59Z"

    events_result = service.events().list(
        calendarId='primary',
        timeMin=start_dt,
        timeMax=end_dt,
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    events = events_result.get('items', [])

    formatted = []
    for event in events:
        summary = event.get('summary', '(No Title)')
        start = event.get('start', {}).get('dateTime', event.get('start', {}).get('date', ''))
        end = event.get('end', {}).get('dateTime', event.get('end', {}).get('date', ''))
        formatted.append({"summary": summary, "start": start, "end": end})

    return formatted

def create_event(summary, start_time, end_time, description="", attendees_emails=None):
    service = get_google_service('calendar', 'v3')

    full_description = f"{description.strip()}\n\n🔗 Zoom Link: {ZOOM_URL}" if ZOOM_URL else description

    event = {
        'summary': summary,
        'description': full_description,
        'start': {'dateTime': start_time, 'timeZone': 'Europe/Paris'},
        'end': {'dateTime': end_time, 'timeZone': 'Europe/Paris'},
        'attendees': [{'email': email.strip()} for email in attendees_emails if email.strip()] if attendees_emails else []
    }

    event = service.events().insert(calendarId='primary', body=event, sendUpdates="all").execute()
    return f"✅ Event created: [{event.get('summary')}]({event.get('htmlLink')})"
