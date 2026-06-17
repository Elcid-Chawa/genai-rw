import yaml
import os
from typing import List, Dict, Any
from collections import Counter

class KnowledgeBaseService:
    def __init__(self):
        self.kb_data = self._load_knowledge_base()
    
    def _load_knowledge_base(self) -> List[Dict[str, Any]]:
        """Load knowledge base from YAML files"""
        kb_data = []
        data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "data")
        
        if not os.path.exists(data_dir):
            return []
        
        for filename in os.listdir(data_dir):
            if filename.endswith('.yml') or filename.endswith('.yaml'):
                filepath = os.path.join(data_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as file:
                        data = yaml.safe_load(file)
                        if isinstance(data, list):
                            kb_data.extend(data)
                        elif isinstance(data, dict):
                            kb_data.append(data)
                except Exception as e:
                    print(f"Error loading {filename}: {e}")
        
        return kb_data
    
    async def search(self, query: str, language: str = "en") -> List[Dict[str, Any]]:
        """Lightweight structured retrieval over YAML entries."""
        if not self.kb_data:
            return []
        
        query_terms = self._terms(query)
        scored = []
        
        for item in self.kb_data:
            content = str(item)
            item_terms = self._terms(content)
            score = sum(item_terms.get(term, 0) for term in query_terms)

            if item.get("language") == language:
                score += 2

            if score > 0:
                result = dict(item)
                result["_score"] = score
                result["_source"] = self._source_for_category(item.get("category"))
                scored.append(result)
        
        scored.sort(key=lambda item: item["_score"], reverse=True)
        return scored[:5]

    async def by_category(self, category: str, language: str = "en") -> List[Dict[str, Any]]:
        matches = [
            dict(item)
            for item in self.kb_data
            if item.get("category") == category and item.get("language", language) == language
        ]

        if not matches and language != "en":
            matches = [dict(item) for item in self.kb_data if item.get("category") == category and item.get("language") == "en"]

        for item in matches:
            item["_source"] = self._source_for_category(item.get("category"))

        return matches

    def get_entry(self, entry_id: str) -> Dict[str, Any] | None:
        for item in self.kb_data:
            if item.get("id") == entry_id:
                result = dict(item)
                result["_source"] = self._source_for_category(item.get("category"))
                return result
        return None
    
    def add_entry(self, entry: Dict[str, Any]) -> bool:
        """Add new entry to knowledge base"""
        try:
            self.kb_data.append(entry)
            return True
        except Exception as e:
            print(f"Error adding entry: {e}")
            return False

    def _terms(self, text: str) -> Counter:
        cleaned = "".join(char.lower() if char.isalnum() else " " for char in text)
        return Counter(term for term in cleaned.split() if len(term) > 2)

    def _source_for_category(self, category: str) -> str:
        sources = {
            "business": "RDB Investment Law 2021",
            "insurance": "RSSB policies and insurance guidance",
            "tourism": "Visit Rwanda 2024 guidelines",
            "farming": "Rwanda agriculture guidance",
            "accessibility": "Rwanda digital accessibility and public-service inclusion guidance",
        }
        return sources.get(category or "", "Unified Government Portal")
