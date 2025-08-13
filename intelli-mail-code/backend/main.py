from fastapi import Request, APIRouter, Body, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import os
from dotenv import load_dotenv
import csv
import json
from fastapi.responses import StreamingResponse
from io import StringIO
from gmail_api import GmailAPI
from gemini_api import GeminiAPI

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
GMAIL_CLIENT_ID = os.getenv("GMAIL_CLIENT_ID")
GMAIL_CLIENT_SECRET = os.getenv("GMAIL_CLIENT_SECRET")
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

@app.get("/")
def root():
    """Health check endpoint"""
    return {"status": "ok"}

@app.get("/api/last5")
def get_last_5_emails():
    """Return last 5 emails from Gmail API"""
    import traceback
    try:
        gmail = GmailAPI()
        user_file = DATA_DIR / "emails.json"
        gmail.authenticate(token_path=str(user_file.with_suffix('.token')))
        emails = gmail.get_recent_emails(max_results=5)
        return {"emails": emails}
    except Exception as e:
        tb = traceback.format_exc()
        print(f"/api/last5 error: {e}\n{tb}")
        return {"emails": [], "error": str(e), "trace": tb}

@app.get("/api/emails")
def get_emails():
    """Return all emails from emails.json"""
    try:
        user_file = DATA_DIR / "emails.json"
        if not user_file.exists():
            return {"emails": []}
        with open(user_file) as f:
            data = json.load(f)
        return {"emails": data.get("emails", [])}
    except Exception as e:
        return {"emails": [], "error": str(e)}

@app.post("/api/generate-summary")
async def generate_summary(email_id: str = Body(...), body: str = Body(...)):
    """Generate summary for an email using GeminiAI"""
    try:
        gemini = GeminiAPI()
        summary_result = gemini.summarize_email(email_content=body)
        summary = summary_result.get('summary', '')
        return {"success": True, "summary": summary}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/gemini-test")
def gemini_test():
    """Test Gemini API connectivity"""
    try:
        gemini = GeminiAPI()
        result = gemini.summarize_email("This is a test email for Gemini API connectivity. Please summarize it.")
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/refresh")
async def refresh_emails():
    """Fetch new emails, summarize, detect replies, and generate drafts"""
    try:
        user_file = DATA_DIR / "emails.json"
        gmail = GmailAPI()
        gmail.authenticate(token_path=str(user_file.with_suffix('.token')))
        gemini = GeminiAPI()

        # Fetch recent emails
        emails = gmail.get_recent_emails(max_results=20)
        processed = []
        for email in emails:
            # Summarize using full body
            summary_result = gemini.summarize_email(email_content=email.get('body', email.get('subject', '')))
            summary = summary_result.get('summary', '')
            # Detect reply
            replied = gmail.check_if_replied(email['thread_id'])
            # Generate draft if not replied
            draft = None
            if not replied:
                draft_result = gemini.generate_draft_reply(email_content=email.get('body', email.get('subject', '')))
                draft = draft_result.get('reply', '')
            processed.append({
                **email,
                'summary': summary,
                'replied': replied,
                'draft': draft
            })

        # Save to user file
        with open(user_file, 'w') as f:
            json.dump({'emails': processed}, f)

        return {"success": True, "emails": processed}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/unreplied-emails")
async def get_unreplied_emails():
    """Return last 5 unreplied emails with AI-generated drafts"""
    try:
        user_file = DATA_DIR / "emails.json"
        if not user_file.exists():
            return {"emails": []}
        with open(user_file) as f:
            data = json.load(f)
        emails = data.get("emails", [])
        # Filter unreplied and sort by timestamp descending, then take last 5
        unreplied = [email for email in emails if not email.get("replied")]
        unreplied = sorted(unreplied, key=lambda e: int(e.get("timestamp", 0)), reverse=True)[:5]
        gemini = GeminiAPI()
        for email in unreplied:
            # Only generate draft if not present
            if not email.get("draft"):
                draft_result = gemini.generate_draft_reply(email_content=email.get("body", email.get("subject", "")))
                email["draft"] = draft_result.get("reply", "")
        return {"emails": unreplied}
    except Exception as e:
        return {"emails": [], "error": str(e)}

@app.post("/api/reply")
async def send_reply(email_id: str = Body(...), reply_text: str = Body(...)):
    """Send a reply and update replied status"""
    try:
        user_file = DATA_DIR / "emails.json"
        gmail = GmailAPI()
        gmail.authenticate(token_path=str(user_file.with_suffix('.token')))
        # Send reply
        sent = gmail.send_reply(thread_id=email_id, message_text=reply_text)
        if not sent:
            return {"success": False, "error": "Failed to send reply via Gmail API"}
        # Update JSON
        if user_file.exists():
            with open(user_file) as f:
                data = json.load(f)
            for email in data.get('emails', []):
                if email['id'] == email_id:
                    email['replied'] = True
            with open(user_file, 'w') as f:
                json.dump(data, f)
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/generate-draft")
async def generate_draft(email_id: str = Body(...), body: str = Body(...)):
    """Generate a draft reply using GeminiAI"""
    try:
        gemini = GeminiAPI()
        draft_result = gemini.generate_draft_reply(email_content=body)
        draft = draft_result.get('reply', '')
        return {"success": True, "draft": draft}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/save-emails")
async def save_emails(request: Request):
    """Save emails from frontend to emails.json"""
    try:
        data = await request.json()
        emails = data.get("emails", [])
        user_file = DATA_DIR / "emails.json"
        with open(user_file, "w") as f:
            json.dump({"emails": emails}, f)
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/export")
async def export_emails():
    """Export emails to CSV"""
    user_file = DATA_DIR / "emails.json"
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=["id", "thread_id", "sender", "subject", "timestamp", "body", "summary", "replied", "draft"])
    writer.writeheader()
    emails = []
    if user_file.exists():
        try:
            with open(user_file) as f:
                content = f.read().strip()
                if content:
                    data = json.loads(content)
                    emails = data.get('emails', [])
        except Exception as e:
            # If file is invalid, just export header with error message row
            writer.writerow({"id": "", "thread_id": "", "sender": "", "subject": "", "timestamp": "", "body": f"Error: {str(e)}", "summary": "", "replied": "", "draft": ""})
            output.seek(0)
            return StreamingResponse(output, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=emails.csv"})
    if not emails:
        writer.writerow({"id": "", "thread_id": "", "sender": "", "subject": "", "timestamp": "", "body": "No emails found.", "summary": "", "replied": "", "draft": ""})
    else:
        for email in emails:
            writer.writerow(email)
    output.seek(0)
    return StreamingResponse(output, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=emails.csv"})

from fastapi import Query

@app.get("/api/unreplied-detect")
def get_unreplied_detect(count: int = Query(5, ge=1, le=50)):
    """Return recent emails (count), each with replied status, AI summary, and AI draft for unreplied."""
    try:
        gmail = GmailAPI()
        gemini = GeminiAPI()
        user_file = DATA_DIR / "emails.json"
        gmail.authenticate(token_path=str(user_file.with_suffix('.token')))
        emails = gmail.get_recent_emails(max_results=count)
        user_profile = gmail.service.users().getProfile(userId='me').execute()
        user_email = user_profile['emailAddress']
        aliases = [user_email]
        try:
            alias_resp = gmail.service.users().settings().sendAs().list(userId='me').execute()
            for alias in alias_resp.get('sendAs', []):
                if alias['sendAsEmail'] not in aliases:
                    aliases.append(alias['sendAsEmail'])
        except Exception:
            pass
        result = []
        for email in emails:
            thread = gmail.service.users().threads().get(userId='me', id=email['thread_id']).execute()
            replied = False
            for msg in thread['messages'][1:]:
                headers = msg['payload']['headers']
                from_header = next((h['value'] for h in headers if h['name'].lower() == 'from'), '')
                if any(alias in from_header for alias in aliases):
                    replied = True
                    break
            email_out = dict(email)
            email_out['replied'] = replied
            # Always generate AI summary
            try:
                summary_result = gemini.summarize_email(email_content=email.get('body', email.get('subject', '')))
                email_out['summary'] = summary_result.get('summary', '')
            except Exception:
                email_out['summary'] = ''
            if not replied:
                # Generate AI draft
                try:
                    draft_result = gemini.generate_draft_reply(email_content=email.get('body', email.get('subject', '')))
                    email_out['draft'] = draft_result.get('reply', '')
                except Exception:
                    email_out['draft'] = ''
            else:
                email_out['draft'] = ''
            result.append(email_out)
        return {"emails": result}
    except Exception as e:
        return {"emails": [], "error": str(e)}


# Main entry point to run the FastAPI application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)