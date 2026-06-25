from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from time import perf_counter
from typing import List, Dict, Any, Optional
import os
from dotenv import load_dotenv

from services.chat_service import ChatService
from services.quote_service import QuoteService
from services.kb_service import KnowledgeBaseService
from services.log_service import LogService
from services.tourism_regulation_service import TourismRegulationService
from services.workflow_service import WorkflowService

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
log_service = LogService()
workflow_service = WorkflowService(kb_service)
tourism_regulation_service = TourismRegulationService()

@app.on_event("startup")
async def startup():
    await log_service.ensure_indexes()

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

class FeedbackRequest(BaseModel):
    interaction_id: Optional[str] = None
    rating: int
    comment: Optional[str] = None
    helpful: Optional[bool] = None

class BusinessPrefillRequest(BaseModel):
    entity_type: Optional[str] = "sole_proprietorship"
    owner_name: Optional[str] = ""
    national_id: Optional[str] = ""
    phone: Optional[str] = ""
    email: Optional[str] = ""
    business_name: Optional[str] = ""
    business_activity: Optional[str] = ""
    business_address: Optional[str] = ""
    language: Optional[str] = "en"

class AgriculturePlanRequest(BaseModel):
    crop: Optional[str] = "maize"
    district: Optional[str] = "Nyamagabe"
    month: Optional[str] = None
    farm_size: Optional[str] = None
    language: Optional[str] = "en"

@app.get("/")
async def root():
    return {"message": "GenAI Rwanda Assistant API"}

@app.post("/chat")
async def chat(request: ChatRequest):
    started_at = perf_counter()
    try:
        response = await chat_service.process_message(
            request.message,
            request.language,
            request.agent,
            request.model,
            request.history,
        )
        response_time_ms = int((perf_counter() - started_at) * 1000)
        interaction_id = await log_service.log_interaction(
            request.model_dump(),
            response,
            response_time_ms,
        )
        response.setdefault("data", {})
        response["data"]["response_time_ms"] = response_time_ms
        response["data"]["interaction_id"] = interaction_id
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

@app.post("/services/quote/insurance")
async def insurance_quote(request: QuoteRequest):
    try:
        return workflow_service.insurance_quote(request.model_dump())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/services/business/requirements")
async def business_requirements(entity_type: str = "sole_proprietorship", language: str = "en"):
    try:
        return await workflow_service.business_requirements(entity_type, language)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/services/business/prefill")
async def business_prefill(request: BusinessPrefillRequest):
    try:
        return await workflow_service.business_prefill(request.model_dump(), request.language)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/services/agriculture/plan")
async def agriculture_plan(request: AgriculturePlanRequest):
    try:
        return await workflow_service.agriculture_plan(request.model_dump(), request.language)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/services/{service}/walkthrough")
async def service_walkthrough(service: str, language: str = "en"):
    try:
        return await workflow_service.service_walkthrough(service, language)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/services/tourism/entities/search")
async def tourism_entities_search(query: str, limit: int = 8):
    try:
        result = tourism_regulation_service.search_licensed_entities(query, limit, force=True)
        return result or {"status": "no_match", "matches": []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/kb/search")
async def search_kb(query: str, lang: str = "en"):
    try:
        results = await kb_service.search(query, lang)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/feedback")
async def feedback(request: FeedbackRequest):
    if request.rating < 1 or request.rating > 5:
        raise HTTPException(status_code=400, detail="rating must be between 1 and 5")

    feedback_id = await log_service.add_feedback(
        request.interaction_id,
        request.rating,
        request.comment,
        request.helpful,
    )
    return {"feedback_id": feedback_id, "stored": feedback_id is not None}

@app.get("/metrics/summary")
async def metrics_summary():
    return await log_service.summary()

@app.get("/logs")
async def logs(limit: int = 25):
    return {"logs": await log_service.recent_logs(limit)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
