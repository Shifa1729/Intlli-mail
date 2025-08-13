
import os
from typing import Dict
from dotenv import load_dotenv
import google.generativeai as genai

class GeminiAPI:
    def __init__(self):
        # Use Gemini API key from environment
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY not set in environment")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-2.0-flash")
        
    def summarize_email(self, email_content: str) -> Dict:
        """Generate a simple, clear, bullet-point summary of the email content."""
        prompt = f"""
        Summarize the following email in 3-5 easy-to-understand bullet points.
        Focus on clarity and relevance. Avoid technical jargon or verbosity.
        Highlight main topics, requests, action items, and deadlines (if any).
        Use plain language suitable for a busy professional.

        Email:
        {email_content}
        """
        try:
            response = self.model.generate_content(prompt)
            return {
                "summary": response.text.strip(),
                "success": True
            }
        except Exception as e:
            return {
                "summary": "",
                "success": False,
                "error": str(e)
            }
    
    def generate_draft_reply(self, email_content: str) -> Dict:
        """Generate a smart, human-sounding draft reply for the email."""
        prompt = f"""
        Write a professional, short, concise, and context-aware reply to the following email.
        The reply should:
        - Sound human and natural, not generic
        - Address all points/questions in the email
        - Be courteous and clear and address the sender's message starting with "Hi" only.
        - Be ready to send as-is and dont include any markdown

        Email thread:
        {email_content}
        """
        try:
            response = self.model.generate_content(prompt)
            return {
                "reply": response.text.strip(),
                "success": True
            }
        except Exception as e:
            return {
                "reply": "",
                "success": False,
                "error": str(e)
            }


def main():
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))
    api = GeminiAPI()
    email_content = "It was great to see you at the conference last week. I really enjoyed our conversation about AI and its future applications. Let's catch up next week to discuss potential collaborations. Best, John Doe"

    summary_result = api.summarize_email(email_content)
    print("Summary Result:", summary_result)

    reply_result = api.generate_draft_reply(email_content)
    print("Reply Result:", reply_result)

if __name__ == "__main__":
    main()