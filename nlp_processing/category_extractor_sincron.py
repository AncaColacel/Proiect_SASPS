import json
import time
from datetime import datetime
import numpy as np
from sentence_transformers import SentenceTransformer, util

# --- 1. PRE-ÎNCĂRCARE ---
print("⏳ Loading model pe CPU...")
# Forțăm rularea pe procesor
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2", device="cpu")

# Definițiile Categoriilor
CATEGORIES = {
    "POLITIC": "politică guvern parlament alegeri ministru lege partid primar consiliu local democrație candidat administrație",
    "SPORT": "sport fotbal liga campionat meci jucător gol tenis handbal baschet antrenor scor echipă trofeu competiție",
    "ECONOMIC": "economie finanțe piață bursă taxe buget salarii inflație afaceri bancă venituri datorie investiții profit",
    "EXTERNE": "internațional relații externe țări uniunea europeană război conflict ambasadă NATO diplomație geopolitică",
    "SOCIAL": "societate educație sănătate familie comunitate populație cultură tradiții viață socială demografie",
    "TEHNOLOGIE": "tehnologie IT AI software internet digital inovare rețea programare industrie tehnologică gadget"
}

cat_names = list(CATEGORIES.keys())
cat_texts = list(CATEGORIES.values())
# Vectorizăm categoriile (se întâmplă rapid, o singură dată)
cat_embeddings = model.encode(cat_texts, convert_to_tensor=True)

# Încărcăm datele brute
INPUT_FILE = "jsons/final/baza_date_final_nlp.json"
try:
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        RAW_DATA = json.load(f)
        if isinstance(RAW_DATA, dict): RAW_DATA = [RAW_DATA]
except:
    RAW_DATA = []

# --- 2. FUNCȚIA CARE BLOCHEAZĂ SERVERUL (Sincronă) ---
def classify_on_demand(start_date_str, end_date_str):
    print(f"⚡ [CPU] Cerere primită: {start_date_str} - {end_date_str}")
    
    # A. Parsare și Filtrare
    try:
        s_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        e_date = datetime.strptime(end_date_str, "%Y-%m-%d")
    except:
        return {"error": "Format dată invalid"}

    articles_to_process = []
    texts_to_encode = []
    
    # Căutăm articolele în JSON-ul brut
    for source in RAW_DATA:
        for art in source.get("articles", []):
            d_str = art.get("date")
            if not d_str: continue
            try:
                d_art = datetime.strptime(d_str.split("T")[0], "%Y-%m-%d")
                if s_date <= d_art <= e_date:
                    title = art.get("title", "")
                    content = art.get("content", "")[:300] 
                    text = f"{title} {content}".strip()
                    
                    if len(text) > 10:
                        art_copy = art.copy()
                        articles_to_process.append(art_copy)
                        texts_to_encode.append(text)
            except: continue

    if not articles_to_process:
        return {"message": "Niciun articol găsit."}

    # =================================================================
    # B. VECTORIZARE PE CPU
    # Aici serverul va munci din greu. Pe CPU, asta e lent.
    # =================================================================
    print(f"🔥 [CPU] Încep vectorizarea a {len(texts_to_encode)} articole...")
    start_t = time.time()
    
    # encode() rulează implicit pe CPU dacă modelul a fost inițializat așa
    article_embeddings = model.encode(texts_to_encode, convert_to_tensor=True)
    
    # Calcul Similaritate
    cosine_scores = util.cos_sim(article_embeddings, cat_embeddings)
    
    # Extragem rezultatele (Tensor -> Numpy -> Int)
    best_cat_indices = cosine_scores.argmax(dim=1).numpy()

    duration = time.time() - start_t
    print(f"⏱️ Gata în {duration:.2f} secunde.")

    # C. Construim răspunsul
    stats = {cat: 0 for cat in cat_names}
    
    for i, art in enumerate(articles_to_process):
        cat_idx = best_cat_indices[i]
        category = cat_names[cat_idx]
        art["category"] = category
        stats[category] += 1

    return {
        "count": len(articles_to_process),
        "processing_time": round(duration, 2),
        "stats": stats,
        "articles": articles_to_process
    }


# --- 3. TEST LOCAL ---
if __name__ == "__main__":
    s = datetime(2025, 10, 1)
    e = datetime(2025, 10, 5)
    classify_on_demand(s.strftime("%Y-%m-%d"), e.strftime("%Y-%m-%d"))
    
