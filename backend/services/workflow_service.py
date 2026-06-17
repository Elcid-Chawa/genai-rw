from datetime import datetime
from typing import Any, Dict, List, Optional

from .kb_service import KnowledgeBaseService
from .quote_service import QuoteService


class WorkflowService:
    def __init__(self, kb_service: Optional[KnowledgeBaseService] = None):
        self.kb_service = kb_service or KnowledgeBaseService()
        self.quote_service = QuoteService()

    async def business_requirements(self, entity_type: str = "sole_proprietorship", language: str = "en") -> Dict[str, Any]:
        entries = await self.kb_service.by_category("business", language)
        entry = self._find_by_field(entries, "entity_type", entity_type) or (entries[0] if entries else {})
        return {
            "service": "business_registration",
            "entity_type": entry.get("entity_type", entity_type),
            "title": entry.get("title", "Business Registration Requirements"),
            "requirements": entry.get("documents", ["National ID", "Business name", "Business address"]),
            "fees": entry.get("fees", "Verify fees with RDB"),
            "timeline": entry.get("timeline", "Verify timeline with RDB"),
            "steps": self._normalize_steps(entry.get("steps", [])),
            "source": entry.get("_source", "RDB Investment Law 2021"),
        }

    async def business_prefill(self, payload: Dict[str, Any], language: str = "en") -> Dict[str, Any]:
        requirements = await self.business_requirements(payload.get("entity_type", "sole_proprietorship"), language)
        fields = {
            "owner_name": payload.get("owner_name", ""),
            "national_id": payload.get("national_id", ""),
            "phone": payload.get("phone", ""),
            "email": payload.get("email", ""),
            "business_name": payload.get("business_name", ""),
            "business_activity": payload.get("business_activity", ""),
            "business_address": payload.get("business_address", ""),
            "entity_type": requirements["entity_type"],
        }
        missing = [key for key, value in fields.items() if key in ["owner_name", "national_id", "business_name", "business_activity"] and not value]
        return {
            "service": "business_registration",
            "title": "Prefilled Business Registration Draft",
            "status": "draft_incomplete" if missing else "draft_ready",
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "fields": fields,
            "missing_fields": missing,
            "requirements": requirements,
            "disclaimer": "This is a prototype draft for demonstration. Confirm official requirements on the RDB portal before submission.",
        }

    def insurance_quote(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        quote = self.quote_service.compute_quote(
            payload.get("vehicle_type", "sedan"),
            int(payload.get("engine_size", 1500)),
            int(payload.get("years_no_claim", 0)),
            payload.get("location", "Kigali"),
        )
        return {
            "service": "insurance_quote",
            "title": "Demo Motor Insurance Quote",
            "input": {
                "vehicle_type": payload.get("vehicle_type", "sedan"),
                "engine_size": int(payload.get("engine_size", 1500)),
                "years_no_claim": int(payload.get("years_no_claim", 0)),
                "location": payload.get("location", "Kigali"),
            },
            "quote": quote,
            "next_steps": [
                "Confirm vehicle registration and ownership details.",
                "Contact a licensed insurer for an official quote.",
                "Keep proof of insurance in the vehicle.",
            ],
            "source": "RSSB policies and insurance guidance",
        }

    async def agriculture_plan(self, payload: Dict[str, Any], language: str = "en") -> Dict[str, Any]:
        crop = (payload.get("crop") or "maize").lower()
        district = (payload.get("district") or "Nyamagabe").lower()
        month = payload.get("month") or datetime.utcnow().strftime("%B")
        entries = await self.kb_service.by_category("farming", language)
        selected = None
        for entry in entries:
            if crop in str(entry.get("crop", "")).lower() and district in str(entry.get("district", "")).lower():
                selected = entry
                break
        selected = selected or (entries[0] if entries else {})
        activities = selected.get("activities", [])
        return {
            "service": "agriculture_plan",
            "title": f"{crop.title()} guidance for {district.title()}",
            "crop": selected.get("crop", crop),
            "district": selected.get("district", district.title()),
            "month": selected.get("month", month),
            "steps": self._normalize_steps(activities),
            "tips": selected.get("tips", "Use local agronomist guidance for final decisions."),
            "checklist": [
                {"item": activity, "done": False}
                for activity in activities
            ],
            "source": selected.get("_source", "Rwanda agriculture guidance"),
        }

    async def service_walkthrough(self, service: str, language: str = "en") -> Dict[str, Any]:
        entries = await self.kb_service.by_category(service, language)
        entry = entries[0] if entries else {}
        steps = entry.get("steps") or entry.get("activities") or []
        return {
            "service": service,
            "title": entry.get("title", f"{service.title()} Walkthrough"),
            "steps": self._normalize_steps(steps),
            "source": entry.get("_source", "Unified Government Portal"),
            "details": entry,
        }

    def _find_by_field(self, entries: List[Dict[str, Any]], field: str, value: str) -> Optional[Dict[str, Any]]:
        normalized = (value or "").lower()
        for entry in entries:
            if str(entry.get(field, "")).lower() == normalized:
                return entry
        return None

    def _normalize_steps(self, steps: List[Any]) -> List[Dict[str, Any]]:
        return [
            {"order": index + 1, "title": str(step), "description": str(step)}
            for index, step in enumerate(steps)
        ]
