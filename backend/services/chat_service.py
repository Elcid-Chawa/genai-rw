import os
from typing import Any, Dict, List

from google import genai
from google.genai import types
from langdetect import detect
from openai import AuthenticationError, OpenAI, RateLimitError

from .automation_service import ServiceAutomationService
from .kb_service import KnowledgeBaseService
from .quote_service import QuoteService
from .tourism_regulation_service import TourismRegulationService
from .workflow_service import WorkflowService


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
    "accessibility": {
        "default_source": "Rwanda digital accessibility and public-service inclusion guidance",
        "context_prompt": (
            "You are an accessibility support assistant for Rwandan digital public services. "
            "Help users access services in simpler language, identify assistive options, "
            "and explain steps for users with disability, low literacy, or limited connectivity."
        ),
    },
}


class ChatService:
    def __init__(self):
        openai_api_key = os.getenv("OPENAI_API_KEY")
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.openai_client = OpenAI(api_key=openai_api_key) if openai_api_key else None
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.gemini_client = genai.Client(api_key=gemini_api_key) if gemini_api_key else None
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        self.kb_service = KnowledgeBaseService()
        self.automation_service = ServiceAutomationService()
        self.tourism_regulation_service = TourismRegulationService()
        self.quote_service = QuoteService()
        self.workflow_service = WorkflowService(self.kb_service)

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
        provider = self._provider_for_model(model)
        selected_model = self._selected_model(model, provider)
        history = history or []

        kb_results = await self.kb_service.search(message, language)
        tool_context = await self._tool_context(message, agent, language)
        automation_context = tool_context.get("automation")
        tourism_entities_context = tool_context.get("tourism_entities")

        if automation_context or tourism_entities_context:
            return {
                "message": self._service_message(tool_context, language),
                "type": "automation" if automation_context else "service_lookup",
                "data": {
                    "automation": automation_context,
                    "tourism_entities": tourism_entities_context,
                    "sources": kb_results,
                    "default_source": self._service_source(tool_context, agent),
                    "tool_context": tool_context,
                    "model": selected_model,
                    "provider": provider,
                },
                "language": language,
            }

        if provider == "gemini" and not self.gemini_client:
            return {
                "message": "Error: Gemini is not configured. Add GEMINI_API_KEY to backend/.env.",
                "type": "error",
                "data": {
                    "model": selected_model,
                    "provider": provider,
                    "reason": "gemini_not_configured",
                    "sources": kb_results,
                    "tool_context": tool_context,
                },
                "language": language,
            }

        if provider == "openai" and not self.openai_client:
            return {
                "message": "OpenAI is not configured. Add OPENAI_API_KEY to backend/.env or choose a Gemini model.",
                "type": "error",
                "data": {
                    "model": selected_model,
                    "provider": provider,
                    "reason": "openai_not_configured",
                    "sources": kb_results,
                    "tool_context": tool_context,
                },
                "language": language,
            }

        try:
            messages = [*history, {"role": "user", "content": message}]
            if provider == "openai":
                content = self._generate_with_openai(
                    messages=messages,
                    agent=agent,
                    language=language,
                    model=selected_model,
                    kb_results=kb_results,
                    tool_context=tool_context,
                )
            else:
                content = self._generate_with_gemini(
                    messages=messages,
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
                    "provider": provider,
                },
                "language": language,
            }
        except RateLimitError:
            return {
                "message": "OpenAI could not process this request because the configured API key has exceeded its quota. Please choose a Gemini model or update OpenAI billing/quota.",
                "type": "error",
                "data": {
                    "model": selected_model,
                    "provider": provider,
                    "reason": "openai_quota_exceeded",
                    "sources": kb_results,
                    "tool_context": tool_context,
                },
                "language": language,
            }
        except AuthenticationError:
            return {
                "message": "OpenAI authentication failed. Please check OPENAI_API_KEY in backend/.env or choose a Gemini model.",
                "type": "error",
                "data": {
                    "model": selected_model,
                    "provider": provider,
                    "reason": "openai_auth_failed",
                    "sources": kb_results,
                    "tool_context": tool_context,
                },
                "language": language,
            }
        except Exception as error:
            print(f"{provider} Error: {type(error).__name__}: {error}")
            return {
                "message": "Error: Unable to connect to the assistant.",
                "type": "error",
                "data": {
                    "model": selected_model,
                    "provider": provider,
                    "reason": type(error).__name__,
                    "sources": kb_results,
                    "tool_context": tool_context,
                },
                "language": language,
            }

    def _provider_for_model(self, model: str = None) -> str:
        return "openai" if (model or "").startswith("gpt-") else "gemini"

    def _selected_model(self, model: str = None, provider: str = "gemini") -> str:
        if model:
            return model
        return self.openai_model if provider == "openai" else self.gemini_model

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

    def _generate_with_openai(
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
        openai_messages = [{"role": "system", "content": system_instruction}]
        openai_messages.extend(self._openai_history(messages[:-1]))
        current_message = messages[-1].get("content", "") if messages else ""
        openai_messages.append({
            "role": "user",
            "content": (
                f"Knowledge base guidance: {kb_results}\n"
                f"Tool context: {tool_context}\n\n"
                f"{current_message}"
            ),
        })

        result = self.openai_client.chat.completions.create(
            model=model,
            messages=openai_messages,
            temperature=0.7,
            max_tokens=800,
        )
        return result.choices[0].message.content or "I'm sorry, I couldn't generate a response."

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
If accessibility, explain service steps in an inclusive, simple, and practical way.
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

    def _openai_history(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        history = []
        for message in messages[-14:]:
            content = message.get("content", "").strip()
            if not content:
                continue

            role = "user" if message.get("role") == "user" else "assistant"
            history.append({"role": role, "content": content})

        return history

    def _detect_language(self, message: str) -> str:
        try:
            detected = detect(message)
            return detected if detected in ["en", "fr", "rw"] else "en"
        except Exception:
            return "en"

    async def _tool_context(self, message: str, agent: str, language: str) -> Dict[str, Any]:
        message_lower = message.lower()
        context: Dict[str, Any] = {}
        automation = await self.automation_service.match(message, agent, language)

        if automation:
            context["automation"] = automation

        if agent in ["general", "tourism"]:
            force_tourism_lookup = agent == "tourism" and any(
                term in message_lower
                for term in ["licensed", "licenced", "registry", "registered", "verify", "check"]
            )
            tourism_entities = self.tourism_regulation_service.search_licensed_entities(
                message,
                force=force_tourism_lookup,
            )
            if tourism_entities:
                context["tourism_entities"] = tourism_entities

        if context:
            return context

        if agent == "insurance" and self._is_insurance_quote_query(message):
            return {
                "insurance_quote": self.workflow_service.insurance_quote(self._extract_quote_payload(message))
            }

        if agent == "business":
            context = {
                "business_requirements": await self.workflow_service.business_requirements(language=language)
            }
            if any(term in message_lower for term in ["form", "prefill", "register", "registration", "company", "business"]):
                context["prefilled_form"] = await self.workflow_service.business_prefill(
                    self._extract_business_payload(message),
                    language,
                )
            return context

        if agent == "farming":
            return {
                "agriculture_plan": await self.workflow_service.agriculture_plan(
                    self._extract_agriculture_payload(message),
                    language,
                )
            }

        if agent == "tourism" and any(term in message_lower for term in ["plan", "tour", "visit", "itinerary", "travel"]):
            return {
                "tourism_walkthrough": await self.workflow_service.service_walkthrough("tourism", language)
            }

        if agent == "accessibility":
            return {
                "accessibility_walkthrough": await self.workflow_service.service_walkthrough("accessibility", language)
            }

        return {}

    def _is_insurance_quote_query(self, message: str) -> bool:
        message_lower = message.lower()
        quote_keywords = ["quote", "premium", "igiciro", "devis"]
        insurance_keywords = ["insurance", "motor", "vehicle", "car", "ubwishingizi", "assurance"]
        return any(keyword in message_lower for keyword in quote_keywords) and any(
            keyword in message_lower for keyword in insurance_keywords
        )

    def _extract_quote_payload(self, message: str) -> Dict[str, Any]:
        message_lower = message.lower()
        vehicle_type = "sedan"
        for candidate in ["suv", "pickup", "hatchback", "sedan"]:
            if candidate in message_lower:
                vehicle_type = candidate

        location = "Kigali" if "kigali" in message_lower else "Rwanda"
        engine_size = 2500 if any(term in message_lower for term in ["2500", "large engine", "big engine"]) else 1500
        years_no_claim = 2 if "no claim" in message_lower or "no-claim" in message_lower else 0

        return {
            "vehicle_type": vehicle_type,
            "engine_size": engine_size,
            "years_no_claim": years_no_claim,
            "location": location,
        }

    def _extract_business_payload(self, message: str) -> Dict[str, Any]:
        entity_type = "limited_company" if "limited" in message.lower() or "company" in message.lower() else "sole_proprietorship"
        return {"entity_type": entity_type}

    def _extract_agriculture_payload(self, message: str) -> Dict[str, Any]:
        message_lower = message.lower()
        crop = "maize"
        for candidate in ["beans", "irish-potatoes", "potatoes", "maize", "ibigori"]:
            if candidate in message_lower:
                crop = "irish-potatoes" if candidate == "potatoes" else candidate

        district = "Nyamagabe"
        for candidate in ["nyamagabe", "musanze", "kigali", "huye", "rubavu"]:
            if candidate in message_lower:
                district = candidate.title()

        return {"crop": crop, "district": district}

    def _service_message(self, tool_context: Dict[str, Any], language: str) -> str:
        sections = []
        if tool_context.get("automation"):
            sections.append(self._automation_message(tool_context["automation"], language))
        if tool_context.get("tourism_entities"):
            sections.append(self._tourism_entities_message(tool_context["tourism_entities"], language))
        return "\n\n".join(section for section in sections if section)

    def _service_source(self, tool_context: Dict[str, Any], agent: str) -> str:
        automation = tool_context.get("automation")
        if automation and automation.get("source"):
            return automation["source"]
        tourism_entities = tool_context.get("tourism_entities")
        if tourism_entities and tourism_entities.get("source_url"):
            return tourism_entities["source_url"]
        return TABS_CONFIG[agent]["default_source"]

    def _automation_message(self, automation: Dict[str, Any], language: str) -> str:
        phrases = {
            "en": {
                "missing": "To continue the service automation, I need:",
                "ready": "I can now prepare the next service steps.",
                "key_checks": "Key checks:",
                "next": "Next actions:",
                "source": "Source",
            },
            "fr": {
                "missing": "Pour continuer l'automatisation du service, j'ai besoin de:",
                "ready": "Je peux maintenant preparer les prochaines etapes du service.",
                "key_checks": "Points cles:",
                "next": "Prochaines actions:",
                "source": "Source",
            },
            "rw": {
                "missing": "Kugira ngo dukomeze iyi serivisi, ndakeneye:",
                "ready": "Ubu nshobora gutegura intambwe zikurikira.",
                "key_checks": "Ibyo kwitaho:",
                "next": "Ibikurikira:",
                "source": "Inkomoko",
            },
        }
        copy = phrases.get(language, phrases["en"])
        lines = [str(automation.get("title", "Service automation"))]

        if automation.get("summary"):
            lines.append(str(automation["summary"]))

        if automation.get("facts"):
            lines.append("")
            lines.append(copy["key_checks"])
            lines.extend([f"- {fact}" for fact in automation["facts"][:4]])

        lines.append("")
        if automation.get("missing_fields"):
            lines.append(copy["missing"])
            for field in automation["missing_fields"]:
                lines.append(f"- {field.get('prompt')}")
        else:
            lines.append(automation.get("ready_message") or copy["ready"])

        if automation.get("next_actions"):
            lines.append("")
            lines.append(copy["next"])
            lines.extend([f"- {action}" for action in automation["next_actions"][:4]])

        source = automation.get("source")
        reviewed = automation.get("last_reviewed")
        if source:
            reviewed_text = f", reviewed {reviewed}" if reviewed else ""
            lines.append("")
            lines.append(f"{copy['source']}: {source}{reviewed_text}")

        return "\n".join(lines)

    def _tourism_entities_message(self, lookup: Dict[str, Any], language: str) -> str:
        phrases = {
            "en": {
                "title": "Licensed tourism entity lookup",
                "matches": "Top matches:",
                "none": "I could not find a matching licensed tourism entity in the cached official registry.",
                "source": "Source",
            },
            "fr": {
                "title": "Recherche d'entites touristiques licenciees",
                "matches": "Meilleurs resultats:",
                "none": "Je n'ai pas trouve de correspondance dans le registre officiel mis en cache.",
                "source": "Source",
            },
            "rw": {
                "title": "Gushaka ibigo by'ubukerarugendo bifite uruhushya",
                "matches": "Ibisubizo bya mbere:",
                "none": "Nta kigo gihuye nabonye muri kopi y'urutonde rwemewe.",
                "source": "Inkomoko",
            },
        }
        copy = phrases.get(language, phrases["en"])
        lines = [copy["title"]]
        message = lookup.get("message")
        if message:
            lines.append(str(message))

        matches = lookup.get("matches", [])
        if matches:
            lines.append("")
            lines.append(copy["matches"])
            for entity in matches[:5]:
                location = ", ".join(
                    part for part in [entity.get("district"), entity.get("province")] if part
                )
                lines.append(
                    f"- {entity.get('name')} ({entity.get('sub_category') or entity.get('category')}, "
                    f"{entity.get('status')}, {location})"
                )
        else:
            lines.append("")
            lines.append(copy["none"])

        source = lookup.get("source_url")
        synced = lookup.get("last_synced")
        if source:
            synced_text = f", synced {synced}" if synced else ""
            lines.append("")
            lines.append(f"{copy['source']}: {source}{synced_text}")

        return "\n".join(lines)
