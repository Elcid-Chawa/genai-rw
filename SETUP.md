# GenAI Rwanda Assistant - Setup Guide

## Prerequisites

- Node.js 18+
- Python 3.8+
- OpenAI API key for generated answers
- Gemini API key if you want to use Google Gemini models

## Backend Setup

From the project root:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `backend/.env` and set:

```dotenv
OPENAI_API_KEY=your_actual_api_key_here
OPENAI_MODEL=gpt-4o-mini
GEMINI_API_KEY=your_actual_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=genai_rw
```

Start the backend:

```powershell
.\.venv\Scripts\python.exe -m uvicorn main:app --reload
```

Backend runs on http://localhost:8000.

## Frontend Setup

From the project root:

```powershell
cd frontend
npm.cmd install
npm.cmd run dev
```

Use `npm.cmd` in PowerShell if script execution policy blocks `npm.ps1`.

Frontend runs on http://localhost:3000.

## Testing the Application

Open http://localhost:3000 and try:

**English**

- "Get me a third-party motor quote for a Toyota in Kigali"
- "Plan a 1-day tour near Musanze on a 50k RWF budget"
- "I grow maize in Nyamagabe; what should I do this month?"
- "How do I register a sole proprietorship?"

**French**

- "Donnez-moi un devis d'assurance pour une Toyota a Kigali"
- "Planifiez une excursion d'une journee pres de Musanze"

**Kinyarwanda**

- "Mpa igiciro cy'ubwishingizi bw'imodoka Toyota i Kigali"
- "Ntegure urugendo rw'umunsi hafi ya Musanze"

## Implemented Features

- Multilingual support (EN/FR/RW)
- Insurance quote calculator
- Tourism itinerary suggestions
- Farming advice by district/crop
- Business registration guidance
- Smart response cards
- Language detection
- Knowledge base search
- Responsive UI

## Notes

- The old `backend/venv` directory may point to a stale Python installation. Use `backend/.venv` for new setup.
- The model picker supports OpenAI models and Gemini models. Gemini selections require `GEMINI_API_KEY`.
- MongoDB settings are present for future session storage, but the current backend does not require MongoDB to start.
- npm may report dependency audit findings. Review those separately before production deployment.
