import json
import time
import os
from datetime import datetime
from sentence_transformers import SentenceTransformer, util

# --- 1. CONFIGURARE MODEL ---
print("⏳ [Sincron] Loading model pe CPU...")
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2", device="cpu")

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
cat_embeddings = model.encode(cat_texts, convert_to_tensor=True)

# --- 2. ÎNCĂRCARE DATE ROBUSTĂ ---
# Aflăm calea folderului PROIECT (urcăm 2 nivele: din nlp_processing -> PROIECT)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Calea către fișierul JSON. 
# ATENȚIE: Verifică dacă la tine e "BAZA_DATE_FINALA.json" sau "BAZA_DATE.json"
INPUT_FILE = os.path.join(BASE_DIR, "jsons", "final", "BAZA_DATE_FINALA.json") 

# Fallback: dacă nu găsește FINALA, caută varianta simplă
if not os.path.exists(INPUT_FILE):
    INPUT_FILE = os.path.join(BASE_DIR, "jsons", "final", "BAZA_DATE.json")

RAW_DATA = []
if os.path.exists(INPUT_FILE):
    try:
        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            RAW_DATA = json.load(f)
            if isinstance(RAW_DATA, dict): RAW_DATA = [RAW_DATA]
        print(f"✅ [Sincron] Baza de date încărcată: {len(RAW_DATA)} surse din {os.path.basename(INPUT_FILE)}")
    except Exception as e:
        print(f"❌ [Sincron] Eroare citire JSON: {e}")
else:
    print(f"⚠️ [Sincron] EROARE CRITICĂ: Nu găsesc fișierul la calea: {INPUT_FILE}")

# --- 3. FUNCȚIA APELATĂ DE SERVER ---
def classify_on_demand(start_date_str, end_date_str):
    print(f"⚡ [CPU] Procesare Sincronă: {start_date_str} - {end_date_str}")
    
    # Template-ul care previne erorile în server
    response_template = {
        "count": 0,
        "processing_time": 0,
        "stats": {k: 0 for k in cat_names},
        "articles": [] # Serverul are nevoie de lista asta, chiar dacă e goală!
    }

    try:
        s_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        e_date = datetime.strptime(end_date_str, "%Y-%m-%d")
    except:
        print("❌ Format dată invalid")
        return {**response_template, "error": "Format dată invalid"}

    articles_to_process = []
    texts_to_encode = []
    
    # Filtrare
    for source in RAW_DATA:
        lista_articole = source.get("articles", []) if isinstance(source, dict) else []
        for art in lista_articole:
            d_str = art.get("date")
            if not d_str: continue
            try:
                d_clean = d_str.split("T")[0]
                d_art = datetime.strptime(d_clean, "%Y-%m-%d")
                
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
        print(f"⚠️ Nu am găsit articole între {start_date_str} și {end_date_str}.")
        # Returnăm structura goală, NU un mesaj de eroare simplu
        return response_template 

    # Vectorizare
    print(f"🔥 [CPU] Încep vectorizarea a {len(texts_to_encode)} articole...")
    start_t = time.time()
    
    try:
        article_embeddings = model.encode(texts_to_encode, convert_to_tensor=True)
        cosine_scores = util.cos_sim(article_embeddings, cat_embeddings)
        best_cat_indices = cosine_scores.argmax(dim=1).numpy()
    except Exception as e:
        print(f"❌ Eroare NLP: {e}")
        return {**response_template, "error": str(e)}

    duration = time.time() - start_t
    print(f"⏱️ Gata în {duration:.2f}s")

    stats = {cat: 0 for cat in cat_names}
    for i, art in enumerate(articles_to_process):
        cat_idx = best_cat_indices[i]
        category = cat_names[cat_idx]
        art["category"] = category
        if "sentiment" not in art: art["sentiment"] = {"label": "neutral"}
        stats[category] += 1

    return {
        "count": len(articles_to_process),
        "processing_time": round(duration, 2),
        "stats": stats,
        "articles": articles_to_process
    }