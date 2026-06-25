import os
import re
from typing import Any, Dict, List, Optional, Tuple

import yaml


class ServiceAutomationService:
    def __init__(self, config_path: Optional[str] = None):
        data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "data")
        self.config_path = config_path or os.path.join(data_dir, "service_automation.yml")
        self.config = self._load_config()
        self.responses = self.config.get("responses", [])

    def _load_config(self) -> Dict[str, Any]:
        if not os.path.exists(self.config_path):
            return {"responses": []}

        try:
            with open(self.config_path, "r", encoding="utf-8") as file:
                data = yaml.safe_load(file) or {}
                return data if isinstance(data, dict) else {"responses": []}
        except Exception as error:
            print(f"Error loading service automation config: {error}")
            return {"responses": []}

    async def match(self, message: str, agent: str = "general", language: str = "en") -> Optional[Dict[str, Any]]:
        query = (message or "").lower()
        if not query:
            return None

        best: Optional[Tuple[int, List[str], Dict[str, Any]]] = None
        for response in self.responses:
            category = response.get("category")
            if agent != "general" and category != agent:
                continue

            score, matched_keywords = self._score_response(response, query)
            if score <= 0:
                continue

            if best is None or score > best[0]:
                best = (score, matched_keywords, response)

        if best is None:
            return None

        score, matched_keywords, response = best
        return self._build_context(response, query, language, score, matched_keywords)

    def _score_response(self, response: Dict[str, Any], query: str) -> Tuple[int, List[str]]:
        matched_keywords: List[str] = []
        intent_score = 0

        for keyword in response.get("intents", {}).get("keywords", []):
            normalized = str(keyword).lower()
            if normalized and normalized in query:
                matched_keywords.append(normalized)
                intent_score += 3 if " " in normalized else 1

        if intent_score <= 0:
            return 0, []

        score = intent_score

        for field in response.get("fields", []):
            for option in field.get("options", []):
                for keyword in option.get("keywords", []):
                    normalized = str(keyword).lower()
                    if normalized and normalized in query:
                        matched_keywords.append(normalized)
                        score += 2

        return score, sorted(set(matched_keywords))

    def _build_context(
        self,
        response: Dict[str, Any],
        query: str,
        language: str,
        score: int,
        matched_keywords: List[str],
    ) -> Dict[str, Any]:
        localized = self._localized(response, language)
        collected_fields = []
        missing_fields = []

        for field in response.get("fields", []):
            value = self._extract_field_value(field, query)
            field_context = {
                "id": field.get("id"),
                "label": field.get("label", field.get("id")),
                "type": field.get("type", "text"),
            }

            if value is not None:
                collected_fields.append({**field_context, "value": value})
            elif field.get("required"):
                missing_fields.append({
                    **field_context,
                    "prompt": field.get("prompt", f"Please provide {field.get('label', field.get('id'))}."),
                    "options": [
                        {"id": option.get("id"), "label": option.get("label", option.get("id"))}
                        for option in field.get("options", [])
                    ],
                })

        service = response.get("service", {})
        status = "needs_input" if missing_fields else "ready"
        return {
            "id": response.get("id"),
            "category": response.get("category"),
            "service_id": response.get("service_id"),
            "status": status,
            "confidence": min(round(score / 10, 2), 1.0),
            "matched_keywords": matched_keywords,
            "title": localized.get("title") or service.get("title") or response.get("service_id"),
            "summary": localized.get("summary", ""),
            "ready_message": localized.get("ready_message", "I have enough information to prepare the service steps."),
            "facts": response.get("facts", []),
            "collected_fields": collected_fields,
            "missing_fields": missing_fields,
            "steps": response.get("steps", []),
            "next_actions": response.get("next_actions", []),
            "source": service.get("source", "Configured service automation"),
            "portal_url": service.get("portal_url"),
            "official_url": service.get("official_url"),
            "last_reviewed": service.get("last_reviewed"),
        }

    def _localized(self, response: Dict[str, Any], language: str) -> Dict[str, str]:
        languages = response.get("languages", {})
        localized = languages.get(language) or languages.get("en") or {}
        return localized if isinstance(localized, dict) else {}

    def _extract_field_value(self, field: Dict[str, Any], query: str) -> Optional[str]:
        for option in field.get("options", []):
            option_keywords = [
                str(option.get("id", "")),
                str(option.get("label", "")),
                *[str(keyword) for keyword in option.get("keywords", [])],
            ]
            if any(keyword.lower() and keyword.lower() in query for keyword in option_keywords):
                return option.get("label", option.get("id"))

        for pattern in field.get("extract", {}).get("patterns", []):
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return match.group(1) if match.groups() else match.group(0)

        return None
