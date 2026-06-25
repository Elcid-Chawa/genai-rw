# GenAI Rwanda Assistant

A multilingual AI assistant for Rwanda supporting Insurance, Tourism, Farming, and Business queries in Kinyarwanda, English, and French.

## Project Structure

```
genai-rw/
├── frontend/          # Next.js frontend
├── backend/           # FastAPI backend
├── data/             # Knowledge base YAML files
└── README.md
```

## Quick Start

### Backend (FastAPI)
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend (Next.js)
```bash
cd frontend
npm install
npm run dev
```

## Features

- Multilingual support (Kinyarwanda, English, French)
- Insurance quotes
- Tourism planning
- Farming advice
- Business registration guidance
- RAG-powered responses with citations
- YAML-driven service automation for deterministic service triage and next steps
- Official tourism license/entity lookup using a cached RDB Tourism Regulation registry sync

See `SERVICE_AUTOMATION.md` for the automation YAML structure.
