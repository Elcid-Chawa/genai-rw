from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
from dotenv import load_dotenv

from services.chat_service import ChatService
from services.quote_service import QuoteService
from services.kb_service import KnowledgeBaseService

load_dotenv()

app = FastAPI(title="GenAI Rwanda Assistant", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
chat_service = ChatService()
quote_service = QuoteService()
kb_service = KnowledgeBaseService()

class ChatRequest(BaseModel):
    message: str
    language: Optional[str] = "en"
    agent: Optional[str] = "general"
    model: Optional[str] = None
    history: Optional[List[Dict[str, str]]] = []

class QuoteRequest(BaseModel):
    vehicle_type: str
    engine_size: int
    years_no_claim: int
    location: str

@app.get("/")
async def root():
    return {"message": "GenAI Rwanda Assistant API"}

@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        response = await chat_service.process_message(
            request.message,
            request.language,
            request.agent,
            request.model,
            request.history,
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/quote")
async def get_quote(request: QuoteRequest):
    try:
        quote = quote_service.compute_quote(
            request.vehicle_type,
            request.engine_size,
            request.years_no_claim,
            request.location
        )
        return quote
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/kb/search")
async def search_kb(query: str, lang: str = "en"):
    try:
        results = await kb_service.search(query, lang)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
