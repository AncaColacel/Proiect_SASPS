import json
import os

folder = "../jsons"  

combined = []

for filename in os.listdir(folder):
    if filename.endswith(".json"):
        filepath = os.path.join(folder, filename)
        
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            combined.append(data)   # păstrează TOT fișierul, metadate + articole

with open("merged.json", "w", encoding="utf-8") as out:
    json.dump(combined, out, ensure_ascii=False, indent=2)

print("✔️ Fișierele au fost unite în merged.json păstrând metadatele.")
