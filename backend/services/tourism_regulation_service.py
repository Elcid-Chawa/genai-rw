import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen


class TourismRegulationService:
    BASE_URL = "https://tourismregulation.rw"
    ENTITIES_ENDPOINT = "https://tourismregulation.rw/en/entities/0/"

    CATEGORY_LABELS = {
        0: "All",
        1: "Accommodation",
        2: "Restaurant/Bar/Nightclub",
        3: "Tour Guide",
        4: "Tour Operator or Travel Agent",
        5: "Tourism Information Office",
        6: "Cultural Tourism or Museum",
    }

    CATEGORY_SUBCATEGORY_TERMS = {
        1: ["hotel", "lodge", "motel", "accommodation", "villa", "cottage", "serviced apartment", "tented camp"],
        2: ["restaurant", "bar", "nightclub"],
        3: ["tour guide"],
        4: ["tour operator", "travel agent"],
        5: ["tourism information"],
        6: ["museum", "cultural tourism"],
    }

    LOCATION_TERMS = {
        "bugesera",
        "burera",
        "gakenke",
        "gasabo",
        "gatsibo",
        "gicumbi",
        "gisagara",
        "huye",
        "kamonyi",
        "karongi",
        "kayonza",
        "kicukiro",
        "kigali",
        "kirehe",
        "muhanga",
        "musanze",
        "ngoma",
        "ngororero",
        "nyabihu",
        "nyagatare",
        "nyamagabe",
        "nyamasheke",
        "nyanza",
        "nyarugenge",
        "nyaruguru",
        "rubavu",
        "ruhango",
        "rulindo",
        "rusizi",
        "rutsiro",
        "rwamagana",
    }

    def __init__(self, cache_path: Optional[str] = None):
        data_dir = Path(__file__).resolve().parents[2] / "data"
        self.cache_path = Path(cache_path) if cache_path else data_dir / "tourism_entities_cache.json"

    def search_licensed_entities(self, query: str, limit: int = 8, force: bool = False) -> Optional[Dict[str, Any]]:
        if not force and not self._is_lookup_query(query):
            return None

        entities = self.load_cached_entities()
        if not entities:
            return {
                "status": "unavailable",
                "title": "Licensed tourism entity lookup",
                "message": "The licensed tourism entity cache is empty. Run the sync script to import the official registry data.",
                "matches": [],
                "source_url": self.ENTITIES_ENDPOINT,
            }

        terms = self._terms(query)
        category_hint = self._category_hint(query)
        scored = []

        for entity in entities:
            score = self._score_entity(entity, terms, category_hint)
            if score > 0:
                scored.append((score, entity))

        scored.sort(key=lambda item: item[0], reverse=True)
        matches = [entity for _, entity in scored[:limit]]

        metadata = self._cache_metadata()
        return {
            "status": "found" if matches else "no_match",
            "title": "Licensed tourism entity lookup",
            "query": query,
            "matches": matches,
            "total_cached": len(entities),
            "source_url": self.ENTITIES_ENDPOINT,
            "last_synced": metadata.get("last_synced"),
            "category_hint": self.CATEGORY_LABELS.get(category_hint) if category_hint is not None else None,
            "message": self._lookup_message(matches, len(entities), metadata.get("last_synced")),
        }

    def load_cached_entities(self) -> List[Dict[str, Any]]:
        if not self.cache_path.exists():
            return []

        try:
            with self.cache_path.open("r", encoding="utf-8") as file:
                payload = json.load(file)
        except Exception as error:
            print(f"Error loading tourism entity cache: {error}")
            return []

        if isinstance(payload, dict):
            entities = payload.get("entities", [])
            return entities if isinstance(entities, list) else []

        return payload if isinstance(payload, list) else []

    def sync_entities(self, page_size: int = 100, category: int = 0) -> Dict[str, Any]:
        first_page = self.fetch_entities(start=0, length=page_size, category=category, draw=1)
        rows = list(first_page.get("data", []))
        records_total = int(first_page.get("recordsTotal") or len(rows))
        records_filtered = int(first_page.get("recordsFiltered") or records_total)

        start = len(rows)
        draw = 2
        while start < records_filtered:
            page = self.fetch_entities(start=start, length=page_size, category=category, draw=draw)
            page_rows = page.get("data", [])
            if not page_rows:
                break
            rows.extend(page_rows)
            start = len(rows)
            draw += 1

        entities = [self._normalize_entity(row) for row in rows]
        entities = [entity for entity in entities if entity.get("name")]
        now = datetime.now(timezone.utc).isoformat()
        cache = {
            "source_url": self.ENTITIES_ENDPOINT,
            "last_synced": now,
            "records_total": records_total,
            "records_filtered": records_filtered,
            "entities": entities,
        }

        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        with self.cache_path.open("w", encoding="utf-8") as file:
            json.dump(cache, file, ensure_ascii=False, indent=2)
            file.write("\n")

        return cache

    def fetch_entities(self, start: int = 0, length: int = 100, category: int = 0, draw: int = 1) -> Dict[str, Any]:
        params = {
            "draw": draw,
            "start": start,
            "length": length,
            "category": category,
        }
        url = f"{self.ENTITIES_ENDPOINT}?{urlencode(params)}"
        request = Request(
            url,
            headers={
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "User-Agent": "GenAI Rwanda service automation demo",
                "X-Requested-With": "XMLHttpRequest",
            },
        )
        with urlopen(request, timeout=30) as response:
            raw = response.read().decode("utf-8")
        return json.loads(raw)

    def _normalize_entity(self, row: List[Any]) -> Dict[str, Any]:
        profile_path = str(row[6]) if len(row) > 6 and row[6] else ""
        return {
            "name": self._clean(row[1] if len(row) > 1 else ""),
            "category": self._clean(row[2] if len(row) > 2 else ""),
            "sub_category": self._clean(row[3] if len(row) > 3 else ""),
            "province": self._clean(row[4] if len(row) > 4 else ""),
            "district": self._clean(row[5] if len(row) > 5 else ""),
            "profile_url": urljoin(self.BASE_URL, profile_path),
            "status": self._clean(row[7] if len(row) > 7 else ""),
        }

    def _cache_metadata(self) -> Dict[str, Any]:
        if not self.cache_path.exists():
            return {}
        try:
            with self.cache_path.open("r", encoding="utf-8") as file:
                payload = json.load(file)
            return payload if isinstance(payload, dict) else {}
        except Exception:
            return {}

    def _score_entity(self, entity: Dict[str, Any], terms: List[str], category_hint: Optional[int]) -> int:
        haystacks = {
            "name": entity.get("name", ""),
            "category": entity.get("category", ""),
            "sub_category": entity.get("sub_category", ""),
            "province": entity.get("province", ""),
            "district": entity.get("district", ""),
            "status": entity.get("status", ""),
        }
        score = 0
        location_terms = [term for term in terms if term in self.LOCATION_TERMS]
        if location_terms:
            location_text = f"{haystacks['province']} {haystacks['district']}".lower()
            if not any(term in location_text for term in location_terms):
                return 0

        if category_hint is not None:
            subcategory_terms = self.CATEGORY_SUBCATEGORY_TERMS.get(category_hint, [])
            entity_subcategory = haystacks["sub_category"].lower()
            entity_category = f"{haystacks['category']} {haystacks['sub_category']}".lower()
            if any(term in entity_subcategory for term in subcategory_terms):
                score += 8
            elif any(term in entity_category for term in subcategory_terms):
                score += 2

        for term in terms:
            variants = self._term_variants(term)
            if any(variant in haystacks["name"].lower() for variant in variants):
                score += 4
            if any(variant in haystacks["sub_category"].lower() for variant in variants):
                score += 3
            if any(variant in haystacks["category"].lower() for variant in variants):
                score += 2
            if any(variant in haystacks["district"].lower() for variant in variants):
                score += 2
            if any(variant in haystacks["province"].lower() for variant in variants):
                score += 1

        if entity.get("status", "").lower() == "licensed":
            score += 1

        return score

    def _is_lookup_query(self, query: str) -> bool:
        normalized = query.lower()
        lookup_markers = [
            "licensed",
            "licenced",
            "registry",
            "registered tourism",
            "check license",
            "verify license",
            "verify licence",
            "licensed entity",
            "licensed entities",
            "show licensed",
            "list licensed",
            "find licensed",
            "is ",
        ]
        tourism_markers = [
            "tourism",
            "tour guide",
            "tour operator",
            "travel agent",
            "hotel",
            "restaurant",
            "bar",
            "nightclub",
            "accommodation",
            "museum",
        ]
        return any(marker in normalized for marker in lookup_markers) and any(
            marker in normalized for marker in tourism_markers
        )

    def _category_hint(self, query: str) -> Optional[int]:
        normalized = query.lower()
        if any(term in normalized for term in ["hotel", "lodge", "motel", "accommodation", "villa", "cottage"]):
            return 1
        if any(term in normalized for term in ["restaurant", "bar", "nightclub"]):
            return 2
        if "tour guide" in normalized or "guide" in normalized:
            return 3
        if "tour operator" in normalized or "travel agent" in normalized or "travel agency" in normalized:
            return 4
        if "information center" in normalized or "information centre" in normalized or "information office" in normalized:
            return 5
        if "museum" in normalized or "cultural tourism" in normalized:
            return 6
        return None

    def _terms(self, text: str) -> List[str]:
        generic = {
            "the",
            "and",
            "for",
            "with",
            "tourism",
            "licensed",
            "licenced",
            "license",
            "licence",
            "entity",
            "entities",
            "show",
            "list",
            "find",
            "check",
            "verify",
            "registered",
            "please",
            "near",
        }
        cleaned = re.sub(r"[^a-z0-9]+", " ", text.lower())
        return [term for term in cleaned.split() if len(term) > 2 and term not in generic]

    def _term_variants(self, term: str) -> set[str]:
        variants = {term}
        if term.endswith("s") and len(term) > 4:
            variants.add(term[:-1])
        return variants

    def _lookup_message(self, matches: List[Dict[str, Any]], total: int, last_synced: Optional[str]) -> str:
        if not matches:
            return "I could not find a matching licensed tourism entity in the cached official registry."

        sync_text = f" synced on {last_synced}" if last_synced else ""
        return f"I found {len(matches)} matching licensed tourism entities from {total} cached official registry records{sync_text}."

    def _clean(self, value: Any) -> str:
        return " ".join(str(value or "").split())
