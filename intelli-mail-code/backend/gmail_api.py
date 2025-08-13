from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from typing import List, Dict
import os
import pickle

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly',
          'https://www.googleapis.com/auth/gmail.send',
          'https://www.googleapis.com/auth/gmail.modify']

class GmailAPI:
    def __init__(self):
        self.creds = None
        self.service = None
        
    def authenticate(self, token_path: str = 'token.pickle'):
        """Authenticate with Gmail API using credentials from .env only."""
        creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if not creds_path or not os.path.exists(creds_path):
            raise RuntimeError(f"Gmail credentials file not found at {creds_path}")

        if os.path.exists(token_path):
            with open(token_path, 'rb') as token:
                self.creds = pickle.load(token)

        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    creds_path, SCOPES)
                self.creds = flow.run_local_server(port=0)
            with open(token_path, 'wb') as token:
                pickle.dump(self.creds, token)

        self.service = build('gmail', 'v1', credentials=self.creds)
        
    def get_recent_emails(self, max_results: int = 20) -> List[Dict]:
        """Get recent emails from Gmail, including plain text body."""
        results = self.service.users().messages().list(
            userId='me', maxResults=max_results).execute()

        messages = []
        for msg in results.get('messages', []):
            email = self.service.users().messages().get(
                userId='me', id=msg['id'], format='full').execute()

            headers = email['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), '')

            # Try to get the plain text body
            body = ''
            payload = email.get('payload', {})
            if 'parts' in payload:
                for part in payload['parts']:
                    if part.get('mimeType') == 'text/plain':
                        data = part['body'].get('data')
                        if data:
                            import base64
                            body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                            break
            elif payload.get('body', {}).get('data'):
                import base64
                body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='ignore')
            if not body:
                body = email.get('snippet', '')

            messages.append({
                'id': email['id'],
                'thread_id': email['threadId'],
                'subject': subject,
                'sender': sender,
                'timestamp': email['internalDate'],
                'body': body
            })

        return messages
    
    def check_if_replied(self, thread_id: str) -> bool:
        """Check if user has replied in the thread."""
        thread = self.service.users().threads().get(
            userId='me', id=thread_id).execute()
        
        user_email = self.service.users().getProfile(userId='me').execute()['emailAddress']
        
        for message in thread['messages'][1:]:  # Skip the first message
            headers = message['payload']['headers']
            from_header = next(h['value'] for h in headers if h['name'] == 'From')
            if user_email in from_header:
                return True
                
        return False
    
    def send_reply(self, thread_id: str, message_text: str) -> bool:
        """Send a reply in the thread."""
        try:
            # Get the thread to reply to
            thread = self.service.users().threads().get(userId='me', id=thread_id).execute()
            messages = thread.get('messages', [])
            if not messages:
                return False
            last_msg = messages[-1]
            headers = last_msg['payload']['headers']
            to = next((h['value'] for h in headers if h['name'].lower() == 'from'), None)
            subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), '')
            msg_id = last_msg['id']

            # Compose reply
            import base64
            from email.mime.text import MIMEText
            from email.utils import formataddr
            user_profile = self.service.users().getProfile(userId='me').execute()
            user_email = user_profile['emailAddress']
            mime_msg = MIMEText(message_text)
            mime_msg['To'] = to
            mime_msg['From'] = user_email
            if subject.lower().startswith('re:'):
                mime_msg['Subject'] = subject
            else:
                mime_msg['Subject'] = f"Re: {subject}"
            mime_msg['In-Reply-To'] = last_msg['id']
            mime_msg['References'] = last_msg['id']

            raw = base64.urlsafe_b64encode(mime_msg.as_bytes()).decode()
            message = {
                'raw': raw,
                'threadId': thread_id
            }
            self.service.users().messages().send(userId='me', body=message).execute()
            return True
        except Exception as e:
            print(f"Error sending reply: {e}")
            return False


# write a main function to test the GmailAPI class
def main():
    import os
    from dotenv import load_dotenv

    load_dotenv()  # Load environment variables from .env file

    gmail_api = GmailAPI()
    gmail_api.authenticate()

    # Get recent emails
    emails = gmail_api.get_recent_emails(max_results=5)
    for email in emails:
        print(f"Subject: {email['subject']}, From: {email['sender']}, Body: {email['body'][:50]}...")

    # Check if replied to the first email thread
    if emails:
        thread_id = emails[0]['thread_id']
        has_replied = gmail_api.check_if_replied(thread_id)
        print(f"Has replied to thread {thread_id}: {has_replied}")

        # Send a reply if not already replied
        if not has_replied:
            reply_text = "Thank you for your email! Let's discuss this further."
            success = gmail_api.send_reply(thread_id, reply_text)
            print(f"Reply sent successfully: {success}")


if __name__ == "__main__":
    main()