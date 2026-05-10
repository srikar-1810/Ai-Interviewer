# InterviewAI - AI-Powered Interview Coach

## Quick Start

### Terminal 1: Backend
```bash
cd AI_INTERVIEWER/backend
python3.11 -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### Terminal 2: Frontend
```bash
cd AI_INTERVIEWER/frontend
npm run dev
```

### Open in Browser
**http://localhost:5173**

---

## Features
- **Register/Login** with email + password or Google OAuth
- **Upload Resume** (PDF, DOCX, TXT) → AI parses skills & infers job roles
- **Job Recommendations** matched to your profile
- **Coaching Setup** (focus areas, difficulty, intensity)
- **Live Interview** with voice or text, adaptive difficulty
- **Analytics** with AI-powered feedback

## Tech Stack
- **Frontend**: React + Vite + TypeScript + Tailwind (port 5173)
- **Backend**: FastAPI + Python 3.11 + Groq LLM (port 8000)
- **Database**: SQLite (local development)
- **AI**: Groq `llama-3.1-8b-instant`
