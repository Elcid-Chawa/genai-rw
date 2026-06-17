import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pymongo import MongoClient
from pymongo.errors import PyMongoError, ServerSelectionTimeoutError


class LogService:
    def __init__(self):
        self.mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        self.database_name = os.getenv("DATABASE_NAME", "genai_rw")
        self.client = MongoClient(self.mongodb_url, serverSelectionTimeoutMS=1200)
        self.db = self.client[self.database_name]
        self.interactions = self.db["interactions"]
        self.feedback = self.db["feedback"]

    async def ping(self) -> bool:
        try:
            self.client.admin.command("ping")
            return True
        except (PyMongoError, ServerSelectionTimeoutError):
            return False

    async def ensure_indexes(self) -> None:
        if not await self.ping():
            return

        self.interactions.create_index("created_at")
        self.interactions.create_index("agent")
        self.interactions.create_index("language")
        self.interactions.create_index("status")
        self.feedback.create_index("interaction_id")
        self.feedback.create_index("created_at")

    async def log_interaction(
        self,
        request: Dict[str, Any],
        response: Dict[str, Any],
        response_time_ms: int,
    ) -> Optional[str]:
        try:
            document = {
                "created_at": datetime.now(timezone.utc),
                "message": request.get("message"),
                "language": request.get("language"),
                "agent": request.get("agent"),
                "model": response.get("data", {}).get("model") or request.get("model"),
                "provider": response.get("data", {}).get("provider"),
                "status": "error" if response.get("type") == "error" else "success",
                "response_time_ms": response_time_ms,
                "response_type": response.get("type"),
                "response_preview": (response.get("message") or "")[:500],
                "sources": self._source_summaries(response.get("data", {}).get("sources", [])),
                "tool_context": response.get("data", {}).get("tool_context", {}),
                "error_reason": response.get("data", {}).get("reason"),
                "history_count": len(request.get("history") or []),
            }
            result = self.interactions.insert_one(document)
            return str(result.inserted_id)
        except PyMongoError as error:
            print(f"MongoDB interaction log skipped: {type(error).__name__}: {error}")
            return None

    async def add_feedback(
        self,
        interaction_id: Optional[str],
        rating: int,
        comment: Optional[str],
        helpful: Optional[bool],
    ) -> Optional[str]:
        try:
            document = {
                "created_at": datetime.now(timezone.utc),
                "interaction_id": interaction_id,
                "rating": rating,
                "comment": comment,
                "helpful": helpful,
            }
            result = self.feedback.insert_one(document)
            return str(result.inserted_id)
        except PyMongoError as error:
            print(f"MongoDB feedback log skipped: {type(error).__name__}: {error}")
            return None

    async def summary(self) -> Dict[str, Any]:
        if not await self.ping():
            return {
                "mongodb_connected": False,
                "message": "MongoDB is not reachable. Start MongoDB or update MONGODB_URL.",
            }

        total = self.interactions.count_documents({})
        successful = self.interactions.count_documents({"status": "success"})
        errors = self.interactions.count_documents({"status": "error"})
        feedback_total = self.feedback.count_documents({})

        avg_response_time = await self._avg("interactions", "response_time_ms")
        avg_rating = await self._avg("feedback", "rating")

        return {
            "mongodb_connected": True,
            "total_interactions": total,
            "successful_interactions": successful,
            "error_interactions": errors,
            "success_rate": round(successful / total, 3) if total else 0,
            "average_response_time_ms": round(avg_response_time or 0, 2),
            "feedback_count": feedback_total,
            "average_rating": round(avg_rating or 0, 2),
            "by_language": await self._count_by("language"),
            "by_agent": await self._count_by("agent"),
            "by_status": await self._count_by("status"),
        }

    async def recent_logs(self, limit: int = 25) -> List[Dict[str, Any]]:
        if not await self.ping():
            return []

        cursor = self.interactions.find({}, {"message": 0}).sort("created_at", -1).limit(limit)
        logs = []
        for item in cursor:
            item["_id"] = str(item["_id"])
            if "created_at" in item:
                item["created_at"] = item["created_at"].isoformat()
            logs.append(item)
        return logs

    async def _avg(self, collection: str, field: str) -> float:
        pipeline = [{"$group": {"_id": None, "avg": {"$avg": f"${field}"}}}]
        result = list(self.db[collection].aggregate(pipeline))
        return result[0]["avg"] if result else 0

    async def _count_by(self, field: str) -> Dict[str, int]:
        pipeline = [
            {"$group": {"_id": f"${field}", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
        ]
        cursor = self.interactions.aggregate(pipeline)
        results = {}
        for item in cursor:
            key = item["_id"] or "unknown"
            results[str(key)] = item["count"]
        return results

    def _source_summaries(self, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        summaries = []
        for source in sources[:5]:
            summaries.append({
                "id": source.get("id"),
                "title": source.get("title"),
                "category": source.get("category"),
                "language": source.get("language"),
            })
        return summaries
