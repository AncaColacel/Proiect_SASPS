import json
import numpy as np
from sentence_transformers import SentenceTransformer, util

# 1. Configurare și Model
print("⏳ Loading model...")
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

CATEGORIES = {
    "POLITIC": "politică guvern parlament alegeri ministru lege partid primar consiliu local democrație candidat administrație",
    "SPORT": "sport fotbal liga campionat meci jucător gol tenis handbal baschet antrenor scor echipă trofeu competiție",
    "ECONOMIC": "economie finanțe piață bursă taxe buget salarii inflație afaceri bancă venituri datorie investiții profit",
    "EXTERNE": "internațional relații externe țări uniunea europeană război conflict ambasadă NATO diplomație geopolitică",
    "SOCIAL": "societate educație sănătate familie comunitate populație cultură tradiții viață socială demografie",
    "TEHNOLOGIE": "tehnologie IT AI software internet digital inovare rețea programare industrie tehnologică gadget"
}

# Pre-calculăm vectorii categoriilor
cat_names = list(CATEGORIES.keys())
cat_texts = list(CATEGORIES.values())
print("🧮 Encoding categories...")
cat_embeddings = model.encode(cat_texts, convert_to_tensor=True)

import os
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
INPUT_FILE = os.path.join(DATA_DIR, "baza_date_final.json")
OUTPUT_FILE = os.path.join(DATA_DIR, "output_classified.json")

# 2. Încărcare Date
print(f"📂 Loading file: {INPUT_FILE}")
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

# 3. Colectare Texte (Flattening)
# Trebuie să ținem minte unde aparține fiecare text (sursa index, articol index)
all_texts = []
mapping = [] # Listă de tupluri (source_idx, article_idx)

print("📝 Preparing texts...")
for s_idx, source in enumerate(data):
    for a_idx, art in enumerate(source.get("articles", [])):
        # Optimizare: Luăm doar titlul și primele 200 caractere din content
        # Modelul are limită de tokens, nu are sens să băgăm tot textul
        title = art.get("title", "")
        content = art.get("content", "")[:300] 
        text = f"{title} {content}".strip()
        
        if len(text) > 10: # Ignorăm articole goale
            all_texts.append(text)
            mapping.append((s_idx, a_idx))

# 4. Procesare Masivă (Batch Encoding) - AICI E VITEZA
print(f"🚀 Encoding {len(all_texts)} articles (Batch Processing)...")
# batch_size=32 sau 64 (depinde de RAM/GPU)
article_embeddings = model.encode(all_texts, batch_size=64, convert_to_tensor=True, show_progress_bar=True)

# 5. Calcul Similaritate (Cosinus)
# Rezultatul e o matrice [nr_articole x nr_categorii]
print("📐 Calculating similarities...")
cosine_scores = util.cos_sim(article_embeddings, cat_embeddings)

# 6. Atribuire Rezultate înapoi în JSON
print("💾 Saving results...")

# Convertim tensorii în numpy pentru a lucra ușor
scores_cpu = cosine_scores.cpu().numpy()

for i, (s_idx, a_idx) in enumerate(mapping):
    # Luăm scorurile pentru articolul i
    art_scores = scores_cpu[i]
    
    # Găsim indexul categoriei maxime
    best_cat_idx = np.argmax(art_scores)
    best_cat_name = cat_names[best_cat_idx]
    
    # Construim dicționarul de scoruri (opțional, dacă vrei să vezi detaliile)
    # score_dict = {cat_names[j]: float(art_scores[j]) for j in range(len(cat_names))}
    
    # Scriem direct în obiectul original din memorie
    data[s_idx]["articles"][a_idx]["category"] = best_cat_name
    # data[s_idx]["articles"][a_idx]["category_scores"] = score_dict # Decomentează dacă vrei toate scorurile

# 7. Salvare Finală
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"✅ Gata! Fișier salvat: {OUTPUT_FILE}")