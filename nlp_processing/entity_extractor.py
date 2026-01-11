import os
import json
from ner_strategies.context import NERProcessor

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')

INPUT_FILE = os.path.join(DATA_DIR, "baza_date_final.json")
OUTPUT_FILE = os.path.join(DATA_DIR, "baza_date_final_with_entities.json")

# Inițializează procesorul NER cu strategia dorită ("regex" sau "transformer")
ner_processor = NERProcessor(strategy_type="regex")  # Schimbă în "transformer" dacă vrei AI

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)


# Suportă atât listă plată de articole, cât și listă de surse cu 'articles'
all_articles = []
if isinstance(data, list):
    # Detectăm dacă e deja o listă plată de articole
    if data and isinstance(data[0], dict) and "content" in data[0]:
        for article in data:
            content_text = article.get("content", "")
            entities = ner_processor.process_text(content_text) if content_text else []
            article["entities"] = entities
            all_articles.append(article)
            print(f"Procesat articol: {article.get('title', 'Fără titlu')}")
    else:
        # Presupunem structură de surse cu 'articles'
        for source in data:
            for article in source.get("articles", []):
                content_text = article.get("content", "")
                entities = ner_processor.process_text(content_text) if content_text else []
                article["entities"] = entities
                all_articles.append(article)
                print(f"Procesat articol: {article.get('title', 'Fără titlu')}")
else:
    print("❌ Format necunoscut pentru baza de date. Nu s-au procesat articole.")

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(all_articles, f, ensure_ascii=False, indent=2)

print(f"Entitățile au fost adăugate și fișierul a fost salvat ca '{OUTPUT_FILE}' (flat list of articles, strategy pattern).")
