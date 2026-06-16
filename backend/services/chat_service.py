import os
from typing import Any, Dict, List

from google import genai
from google.genai import types
from langdetect import detect

from .kb_service import KnowledgeBaseService
from .quote_service import QuoteService


TABS_CONFIG = {
    "general": {
        "default_source": "Unified Government Portal",
        "context_prompt": (
            "You are the Rwandan Unified Service Assistant. You are helpful, "
            "professional, and provide general information about Rwanda."
        ),
    },
    "business": {
        "default_source": "RDB Investment Law 2021",
        "context_prompt": (
            "You are an expert on Rwandan Business Law and RDB/RRA procedures. "
            'Always refer to "RDB Investment Law 2021".'
        ),
    },
    "tourism": {
        "default_source": "Visit Rwanda 2024 guidelines",
        "context_prompt": (
            "You are an expert guide for Rwanda tourism. Always refer to "
            '"Visit Rwanda 2024 guidelines".'
        ),
    },
    "insurance": {
        "default_source": "RSSB Guidelines and Regulations",
        "context_prompt": (
            "You are an expert on Rwandan Social Security and insurance in Rwanda. "
            "Help users with RSSB, Mutuelle de Sante, pension, and motor insurance information."
        ),
    },
    "farming": {
        "default_source": "Rwanda agriculture guidance",
        "context_prompt": (
            "You are a Rwanda-focused farming advisor. Help users with crop, district, "
            "seasonal, pest, fertilizer, and market-readiness guidance."
        ),
    },
}


class ChatService:
    def __init__(self):
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.gemini_client = genai.Client(api_key=gemini_api_key) if gemini_api_key else None
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-3-flash-preview")
        self.kb_service = KnowledgeBaseService()
        self.quote_service = QuoteService()

    async def process_message(
        self,
        message: str,
        language: str = None,
        agent: str = "general",
        model: str = None,
        history: List[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        language = language or self._detect_language(message)
        agent = agent if agent in TABS_CONFIG else "general"
        selected_model = model if (model or "").startswith("gemini-") else self.gemini_model
        history = history or []

        kb_results = await self.kb_service.search(message, language)
        tool_context = self._tool_context(message, agent)

        if not self.gemini_client:
            return {
                "message": "Error: Gemini is not configured. Add GEMINI_API_KEY to backend/.env.",
                "type": "error",
                "data": {
                    "model": selected_model,
                    "provider": "gemini",
                    "reason": "gemini_not_configured",
                    "sources": kb_results,
                    "tool_context": tool_context,
                },
                "language": language,
            }

        try:
            content = self._generate_with_gemini(
                messages=[
                    *history,
                    {"role": "user", "content": message},
                ],
                agent=agent,
                language=language,
                model=selected_model,
                kb_results=kb_results,
                tool_context=tool_context,
            )

            return {
                "message": content,
                "type": "general",
                "data": {
                    "sources": kb_results,
                    "default_source": TABS_CONFIG[agent]["default_source"],
                    "tool_context": tool_context,
                    "model": selected_model,
                    "provider": "gemini",
                },
                "language": language,
            }
        except Exception as error:
            print(f"Gemini Error: {type(error).__name__}: {error}")
            return {
                "message": "Error: Unable to connect to the assistant.",
                "type": "error",
                "data": {
                    "model": selected_model,
                    "provider": "gemini",
                    "reason": type(error).__name__,
                    "sources": kb_results,
                    "tool_context": tool_context,
                },
                "language": language,
            }

    def _generate_with_gemini(
        self,
        messages: List[Dict[str, str]],
        agent: str,
        language: str,
        model: str,
        kb_results: List[Dict[str, Any]],
        tool_context: Dict[str, Any],
    ) -> str:
        config = TABS_CONFIG[agent]
        system_instruction = self._system_instruction(config["context_prompt"], language)
        chat_history = self._gemini_history(messages)
        current_message = chat_history.pop()["parts"][0]["text"] if chat_history else ""

        guided_prompt = (
            f"Knowledge base guidance: {kb_results}\n"
            f"Tool context: {tool_context}\n\n"
            f"{current_message}"
        )

        result = self.gemini_client.models.generate_content(
            model=model,
            contents=[
                *chat_history,
                {"role": "user", "parts": [{"text": guided_prompt}]},
            ],
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.7,
            ),
        )

        return result.text or "I'm sorry, I couldn't generate a response."

    def _system_instruction(self, context_prompt: str, language: str) -> str:
        language_name = {
            "en": "English",
            "fr": "French",
            "rw": "Kinyarwanda",
        }.get(language, "English")

        return f"""
{context_prompt}
Language: {language_name}.
User's current language preference is {language}. Please respond in that language.
If the user asks about business, strictly refer to 'RDB Investment Law 2021'.
If tourism, refer to 'Visit Rwanda 2024 guidelines'.
If insurance, refer to RSSB policies.
If farming, use Rwanda-focused agricultural guidance from the provided context.
The knowledge base is only a guide for AI-generated responses, not a script.
Always cite the source at the end of your response if applicable.
Keep responses helpful, professional, and clear.
"""

    def _gemini_history(self, messages: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        chat_history = []
        for message in messages[-14:]:
            content = message.get("content", "").strip()
            if not content:
                continue

            role = "user" if message.get("role") == "user" else "model"
            chat_history.append({"role": role, "parts": [{"text": content}]})

        return chat_history

    def _detect_language(self, message: str) -> str:
        try:
            detected = detect(message)
            return detected if detected in ["en", "fr", "rw"] else "en"
        except Exception:
            return "en"

    def _tool_context(self, message: str, agent: str) -> Dict[str, Any]:
        if agent == "insurance" and self._is_insurance_quote_query(message):
            return {
                "insurance_quote_demo": self.quote_service.compute_quote("sedan", 1500, 2, "Kigali")
            }

        return {}

    def _is_insurance_quote_query(self, message: str) -> bool:
        message_lower = message.lower()
        quote_keywords = ["quote", "premium", "igiciro", "devis"]
        insurance_keywords = ["insurance", "motor", "vehicle", "car", "ubwishingizi", "assurance"]
        return any(keyword in message_lower for keyword in quote_keywords) and any(
            keyword in message_lower for keyword in insurance_keywords
        )
