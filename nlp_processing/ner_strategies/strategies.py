from abc import ABC, abstractmethod
import re

# --- 1. INTERFAȚA (Abstract Base Class) ---
class NERStrategy(ABC):
    @abstractmethod
    def extract(self, text):
        """Metoda pe care orice strategie trebuie să o aibă."""
        pass

# --- 2. CONCRETE STRATEGY A: REGEX (Simplă) ---
class RegexStrategy(NERStrategy):
    def extract(self, text):
        # Caută doar cuvinte care încep cu literă mare
        pattern = r'\b[A-ZĂÎÂȘȚ][a-zjxăîâșț]+\b'
        matches = re.findall(pattern, text)
        return [{"text": m, "type": "GENERIC"} for m in set(matches)]

# --- 3. CONCRETE STRATEGY B: TRANSFORMER (Complexă) ---
class TransformerStrategy(NERStrategy):
    def __init__(self):
        print("   [NER Engine] Încărcare model Transformer (poate dura puțin)...")
        try:
            from transformers import pipeline
            # Folosim un model mic și rapid pentru demonstrație
            self.pipe = pipeline("ner", model="Babelscape/wikineural-multilingual-ner", aggregation_strategy="simple")
            self.active = True
        except Exception as e:
            print(f"   [Eroare] Modelul nu a putut fi încărcat: {e}")
            self.active = False

    def extract(self, text):
        if not self.active:
            return []
        
        # Procesăm textul
        results = self.pipe(text[:512]) # Limităm la 512 caractere
        
        # Formatăm frumos rezultatul
        entities = []
        for res in results:
            if res['score'] > 0.50: # Filtru de încredere
                entities.append({
                    "text": res['word'],
                    "type": res['entity_group']  # PER, LOC, ORG
                })
        
        # Eliminăm duplicatele bazate pe text
        unique_entities = {e['text']: e for e in entities}.values()
        return list(unique_entities)
