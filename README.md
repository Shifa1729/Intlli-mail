
# Smart Email Assistant Tool 

## 1. Technology Stack

| Technology                | Used For                                      
|---------------------------|-----------------------------------------------
| FastAPI                   | Backend API server                            
| Uvicorn                   | ASGI server for running FastAPI               
| Python dotenv             | Loading environment variables                 
| Google API Python Client  | Gmail API integration                        
| Google Auth, OAuthlib     | Gmail OAuth2 authentication                   
| Google GenerativeAI       | Gemini AI summarization & draft generation    
| React (Vite, TypeScript)  | Frontend SPA (Dashboard UI)                   
| Axios                     | HTTP requests from frontend to backend        
| CSV/JSON                  | Data storage and export                       

---

## 2. Use Cases
1. **Summarize Emails**  
   - User clicks "Refresh" - app fetches latest emails and shows bullet-point summaries.
2. **Detect Replies**  
   - App checks if the user has replied in the email thread and shows status in the dashboard.
3. **Generate Drafts**  
   - For unreplied emails, app creates a draft reply automatically. For replied emails, user can generate a draft if needed.
4. **Send Reply**  
   - User reviews and sends the draft; app marks the email as replied.
5. **Export CSV**  
   - User exports the email list with summaries, statuses, and drafts.

---

## 2. System Architecture

```
React SPA (Dashboard)  <-->  FastAPI API  <-->  JSON Files on Disk
     ^                       |
     |                       +--> Gmail API
     |                       +--> Gemini API
     v
   User
```

- **Frontend (React)**  
  - Single page: Dashboard (email list, summaries, reply status, draft, export)
- **Backend (FastAPI)**  

- **Storage**  
  - Flat JSON file: `data/emails.json`


