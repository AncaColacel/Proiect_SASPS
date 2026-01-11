
import json
import os

folder = "data/"
os.makedirs(folder, exist_ok=True)

all_articles = []
json_files = [f for f in os.listdir(folder) if f.endswith(".json")]

if not json_files:
    print(f"[WARN] Nu există fișiere .json de îmbinat în {folder}. Nicio acțiune efectuată.")
else:
    for filename in json_files:
        filepath = os.path.join(folder, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            # If data is a dict with 'articles', extend with those and add source
            if isinstance(data, dict) and "articles" in data:
                for article in data["articles"]:
                    article["source"] = filename.replace('.json', '')
                    all_articles.append(article)
            # If data is a list, extend directly and add source
            elif isinstance(data, list):
                for article in data:
                    if isinstance(article, dict):
                        article["source"] = filename.replace('.json', '')
                    all_articles.append(article)
            # Otherwise, skip
    with open("data/baza_date_final.json", "w", encoding="utf-8") as out:
        json.dump(all_articles, out, ensure_ascii=False, indent=2)
    print("✔️ Fișierele au fost unite în baza_date_final.json ca listă de articole.")
