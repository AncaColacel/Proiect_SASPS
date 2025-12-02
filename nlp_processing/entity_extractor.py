import json
import roner

# Inițializează modelul RoNER cu named_persons_only pentru a include doar nume proprii
ner = roner.NER(named_persons_only=True)

# Încarcă fișierul JSON cu articole
with open("../jsons/final/baza_date_final.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Iterează prin fiecare sursă și fiecare articol
for source in data:
    for article in source.get("articles", []):
        content_text = article.get("content", "")
        
        # Rulează NER pe conținut
        ner_output = ner([content_text])[0]  # RoNER returnează o listă, luăm primul element
        
        # Grupăm entitățile, combinând multi-word entities
        entities = {}
        current_entity = None
        current_tag = None
        
        for word_info in ner_output["words"]:
            tag = word_info["tag"]
            text = word_info["text"]
            
            if tag == "O":
                # dacă eram pe o entitate multi-word, salvăm ce am strâns
                if current_entity:
                    if current_tag not in entities:
                        entities[current_tag] = []
                    entities[current_tag].append(current_entity)
                    current_entity = None
                    current_tag = None
                continue

            if word_info.get("multi_word_entity", False):
                # Continuăm entitatea curentă
                current_entity += " " + text
            else:
                # Dacă avem o entitate curentă, o salvăm
                if current_entity:
                    if current_tag not in entities:
                        entities[current_tag] = []
                    entities[current_tag].append(current_entity)
                # Începem o nouă entitate
                current_entity = text
                current_tag = tag

        # La final, salvăm ultima entitate dacă există
        if current_entity:
            if current_tag not in entities:
                entities[current_tag] = []
            entities[current_tag].append(current_entity)

        # Eliminăm duplicatele și sortăm
        for tag in entities:
            entities[tag] = sorted(list(set(entities[tag])))

        # Adăugăm noul câmp în articol
        print(f"Procesat articol: {article.get('title', 'Fără titlu')}")
        article["entities"] = entities

# Salvăm rezultatul într-un nou fișier JSON
with open("../jsons/final/baza_date_final_with_entities.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Entitățile au fost adăugate, duplicatele eliminate și fișierul a fost salvat ca 'baza_date_with_topics_with_entities.json'.")