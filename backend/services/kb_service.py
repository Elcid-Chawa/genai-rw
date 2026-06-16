import yaml
import os
from typing import List, Dict, Any

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
        """Simple keyword-based search (mock RAG)"""
        if not self.kb_data:
            return []
        
        query_lower = query.lower()
        results = []
        
        for item in self.kb_data:
            # Simple keyword matching
            content = str(item).lower()
            if any(word in content for word in query_lower.split()):
                results.append(item)
        
        # Return top 4 results
        return results[:4]
    
    def add_entry(self, entry: Dict[str, Any]) -> bool:
        """Add new entry to knowledge base"""
        try:
            self.kb_data.append(entry)
            return True
        except Exception as e:
            print(f"Error adding entry: {e}")
            return False
