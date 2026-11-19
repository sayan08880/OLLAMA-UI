
import os
import base64

from html.parser import HTMLParser
from email.utils import parseaddr
from email.message import EmailMessage

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from hulk.config import (
    GMAIL_CLIENT_FILE,
    GMAIL_TOKEN_FILE,
    GMAIL_MAX_READ
)


# Gmail API permissions
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.compose"
]

MAX_EMAIL_CHARS = 5000


# HTML to text converter
class HTMLText(HTMLParser):

    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        if data.strip():
            self.parts.append(data.strip())

    def text(self):
        return " ".join(self.parts)


# Save OAuth token securely
def save_token(creds):

    token_directory = os.path.dirname(
        os.path.abspath(GMAIL_TOKEN_FILE)
    )

    os.makedirs(token_directory, exist_ok=True)

    with open(GMAIL_TOKEN_FILE, "w") as file:
        file.write(creds.to_json())

    os.chmod(GMAIL_TOKEN_FILE, 0o600)


# Load and refresh Gmail credentials
def get_credentials():

    if not os.path.exists(GMAIL_TOKEN_FILE):
        raise RuntimeError(
            "Gmail is not connected. Select Connect Gmail first."
        )

    creds = Credentials.from_authorized_user_file(
        GMAIL_TOKEN_FILE,
        SCOPES
    )

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        save_token(creds)

    if not creds.valid:
        raise RuntimeError(
            "Gmail authorization is invalid. Reconnect Gmail."
        )

    return creds


# Build Gmail API service
def get_service():

    creds = get_credentials()

    return build(
        "gmail",
        "v1",
        credentials=creds,
        cache_discovery=False
    )


# Check Gmail connection
def gmail_connection_status():

    try:

        service = get_service()

        profile = service.users().getProfile(
            userId="me"
        ).execute()

        email_address = profile.get(
            "emailAddress",
            "Unknown account"
        )

        return True, f"Gmail connected: {email_address}"

    except Exception as error:

        return False, f"Gmail connection failed: {error}"


# Connect Gmail using Google OAuth
def connect_gmail():

    creds = None

    if os.path.exists(GMAIL_TOKEN_FILE):

        creds = Credentials.from_authorized_user_file(
            GMAIL_TOKEN_FILE,
            SCOPES
        )

    if creds and creds.expired and creds.refresh_token:

        creds.refresh(Request())

    if not creds or not creds.valid:

        if not os.path.exists(GMAIL_CLIENT_FILE):

            raise FileNotFoundError(
                f"{GMAIL_CLIENT_FILE} not found. "
                "Download Google OAuth Desktop credentials."
            )

        flow = InstalledAppFlow.from_client_secrets_file(
            GMAIL_CLIENT_FILE,
            SCOPES
        )

        creds = flow.run_local_server(
            port=0,
            access_type="offline",
            prompt="consent"
        )

    save_token(creds)

    service = build(
        "gmail",
        "v1",
        credentials=creds,
        cache_discovery=False
    )

    service.users().getProfile(
        userId="me"
    ).execute()

    return service


# Decode Gmail base64 message body
def decode_email_body(data):

    try:

        data += "=" * (-len(data) % 4)

        decoded = base64.urlsafe_b64decode(data)

        return decoded.decode(
            "utf-8",
            errors="replace"
        )

    except Exception:

        return ""


# Extract email body
def extract_email_body(payload):

    plain = []
    html = []

    def walk(part):

        if part.get("filename"):
            return

        mime = part.get("mimeType", "")

        data = part.get(
            "body",
            {}
        ).get("data")

        if data:

            decoded = decode_email_body(data)

            if mime == "text/plain":
                plain.append(decoded)

            elif mime == "text/html":
                html.append(decoded)

        for child in part.get("parts", []):
            walk(child)

    walk(payload)

    if plain:
        return "\n".join(plain)

    if html:

        parser = HTMLText()

        parser.feed("\n".join(html))

        return parser.text()

    return "(No readable message body.)"


# Get email header
def get_header(headers, name, default=""):

    return next(
        (
            header.get("value", "")
            for header in headers
            if header.get("name", "").lower() == name.lower()
        ),
        default
    )


# Fetch latest Gmail emails
def fetch_latest_emails(requested_count):

    limit = GMAIL_MAX_READ

    if requested_count < 1:
        raise ValueError("Email count must be at least 1.")

    if requested_count > limit:

        print(
            f"\nSorry boss, my Gmail read limit is {limit}. "
            f"You asked for {requested_count}, "
            f"so I'll analyse only {limit} emails.\n"
        )

    count = min(requested_count, limit)

    service = get_service()

    listed = service.users().messages().list(
        userId="me",
        maxResults=count,
        q="in:anywhere -in:trash"
    ).execute()

    message_ids = listed.get("messages", [])

    emails = []

    for index, item in enumerate(message_ids, 1):

        message = service.users().messages().get(
            userId="me",
            id=item["id"],
            format="full"
        ).execute()

        payload = message.get("payload", {})

        headers = payload.get("headers", [])

        sender = get_header(
            headers,
            "From",
            "Unknown sender"
        )

        email_data = {

            "number": index,

            "id": item["id"],

            "thread_id": message.get(
                "threadId",
                ""
            ),

            "from": sender,

            "sender_email": parseaddr(sender)[1],

            "to": get_header(headers, "To"),

            "date": get_header(headers, "Date"),

            "subject": get_header(
                headers,
                "Subject",
                "(No subject)"
            ),

            "body": extract_email_body(
                payload
            )[:MAX_EMAIL_CHARS]
        }

        emails.append(email_data)

    return emails


# Create and save a Gmail draft
def create_gmail_draft(recipient, subject, body):

    """
    Save an email in Gmail Drafts.

    This function NEVER sends an email.
    """

    recipient = recipient.strip()
    subject = subject.strip()
    body = body.strip()

    if not recipient:
        raise ValueError("Recipient email is required.")

    if not subject:
        raise ValueError("Email subject is required.")

    if not body:
        raise ValueError("Email body is required.")

    service = get_service()

    # Create email message
    message = EmailMessage()

    message["To"] = recipient
    message["Subject"] = subject

    message.set_content(body)

    # Encode email message
    encoded_message = base64.urlsafe_b64encode(
        message.as_bytes()
    ).decode("utf-8")

    draft_body = {

        "message": {
            "raw": encoded_message
        }

    }

    # Save draft in Gmail
    result = service.users().drafts().create(
        userId="me",
        body=draft_body
    ).execute()

    draft_id = result.get("id")

    if not draft_id:
        raise RuntimeError(
            "Gmail did not return a draft ID."
        )

    return draft_id
