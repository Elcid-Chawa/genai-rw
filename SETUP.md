# GenAI Rwanda Assistant - Setup Guide

## Prerequisites

- Node.js 18+
- Python 3.8+
- Gemini API key for generated answers
- OpenAI API key if you want to test OpenAI models
- MongoDB running locally or a MongoDB Atlas connection string for evaluation logs

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
GEMINI_API_KEY=your_actual_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
OPENAI_API_KEY=your_actual_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=genai_rw
```

Start the backend:

```powershell
.\.venv\Scripts\python.exe -m uvicorn main:app --reload
```

Backend runs on http://localhost:5000.

## Frontend Setup

From the project root:

```powershell
cd frontend
npm.cmd install
npm.cmd run dev
```

Use `npm.cmd` in PowerShell if script execution policy blocks `npm.ps1`.

Frontend runs on http://localhost:3008.

## Testing the Application

Open http://localhost:3008 and try:

**English**

- "Get me a third-party motor quote for a Toyota in Kigali"
- "Plan a 1-day tour near Musanze on a 50k RWF budget"
- "I grow maize in Nyamagabe; what should I do this month?"
- "How do I register a sole proprietorship?"
- "Explain how a user with low literacy can access public services online"

**French**

- "Donnez-moi un devis d'assurance pour une Toyota a Kigali"
- "Planifiez une excursion d'une journee pres de Musanze"

**Kinyarwanda**

- "Mpa igiciro cy'ubwishingizi bw'imodoka Toyota i Kigali"
- "Ntegure urugendo rw'umunsi hafi ya Musanze"

## Implemented Features

- Multilingual support (EN/FR/RW)
- Insurance quote calculator and quotation workflow
- Tourism walkthrough support
- Farming advice by district/crop
- Business registration guidance and prefilled form drafts
- Accessibility support
- Smart response cards
- Language detection
- Knowledge base search
- Responsive UI

## Notes

- The old `backend/venv` directory may point to a stale Python installation. Use `backend/.venv` for new setup.
- The backend chat service supports Gemini and OpenAI. Gemini remains the default; OpenAI models require `OPENAI_API_KEY` and active quota/billing.
- MongoDB stores interaction logs, feedback, and evaluation metrics. The app can still answer if MongoDB is down, but `/metrics/summary` will report that MongoDB is not reachable.
- Service delivery endpoints:
  - `POST /services/quote/insurance`
  - `GET /services/business/requirements`
  - `POST /services/business/prefill`
  - `POST /services/agriculture/plan`
  - `GET /services/{service}/walkthrough`
- Evaluation endpoints:
  - `GET /metrics/summary`
  - `GET /logs?limit=25`
  - `POST /feedback`
- npm may report dependency audit findings. Review those separately before production deployment.
