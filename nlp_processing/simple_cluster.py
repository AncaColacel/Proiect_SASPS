import json
import difflib
import time
import os
from datetime import datetime

# --- CONFIGURARE ---
# Fișierul care are deja sentimente și entități (dar nu are clustere)
INPUT_FILE = "jsons/final/BAZA_DATE.json"
# Fișierul rezultat (va fi identic, dar cu câmpul 'cluster_id' adăugat)
OUTPUT_FILE = "jsons/final/BAZA_DATE_FINAL.json"

# Pragul de similaritate (0.60 = 60%)
SIMILARITY_THRESHOLD = 0.60

def run_clustering():
    start_time = time.time()
    print(f"📂 [LOAD] Citesc datele din {INPUT_FILE}...")

    # 1. ÎNCĂRCARE DATE
    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            # Flatten: Transformăm în listă simplă de articole dacă e cazul
            if isinstance(data, dict): 
                # Dacă e formatul nou {metadata:..., articles: [...]}
                raw_articles = data.get("articles", [])
            else:
                # Dacă e lista veche de surse [{source:..., articles:[...]}]
                raw_articles = []
                for src in data: 
                    raw_articles.extend(src.get("articles", []))
    except Exception as e:
        print(f"❌ Eroare citire: {e}")
        return

    total_arts = len(raw_articles)
    print(f"🚀 [START] Încep gruparea a {total_arts} articole...")
    print(f"   (Metoda: SequenceMatcher > {SIMILARITY_THRESHOLD})")

    # 2. LOGICA DE CLUSTERING (cea cerută de tine)
    # Lista de clustere. Fiecare element e un dict: 
    # {'id': 1, 'rep_title': 'Titlu reprezentativ', 'articles': [art1, art2]}
    clusters = []
    next_cluster_id = 1

    processed_count = 0

    for art in raw_articles:
        current_title = art.get("title", "")
        if not current_title: continue

        found_cluster_id = None

        # --- AICI E LOGICA TA ---
        # Comparăm articolul curent cu "reprezentantul" fiecărui cluster existent
        for cluster in clusters:
            rep_title = cluster['rep_title']
            
            # Comparație lentă de text (exact cum ai cerut)
            similarity = difflib.SequenceMatcher(None, rep_title, current_title).ratio()
            
            if similarity > SIMILARITY_THRESHOLD:
                # BINGO! Am găsit grupul
                found_cluster_id = cluster['id']
                # Dacă titlul curent e mai lung, îl facem pe el reprezentativ (opțional, dar util)
                if len(current_title) > len(rep_title):
                    cluster['rep_title'] = current_title
                break
        
        # --- ATRIBUIRE ID ---
        if found_cluster_id:
            # Îl marcăm cu ID-ul găsit
            art["cluster_id"] = found_cluster_id
        else:
            # Creăm cluster nou
            new_id = next_cluster_id
            next_cluster_id += 1
            
            clusters.append({
                'id': new_id,
                'rep_title': current_title
            })
            art["cluster_id"] = new_id

        # Logging progres
        processed_count += 1
        if processed_count % 100 == 0:
            print(f"   ... procesat {processed_count}/{total_arts} | Clustere găsite: {len(clusters)}")

    # 3. SALVARE
    print(f"💾 [SAVE] Salvez {len(raw_articles)} articole grupate în {len(clusters)} subiecte...")
    
    # Păstrăm structura plată, ușor de citit de server
    final_output = {
        "metadata": {
            "generated_at": str(datetime.now()),
            "total_articles": len(raw_articles),
            "total_clusters": len(clusters),
            "method": "difflib_simple"
        },
        "articles": raw_articles
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(final_output, f, ensure_ascii=False, indent=2)

    duration = time.time() - start_time
    print(f"✅ [DONE] Gata în {duration:.2f} secunde. Fișier: {OUTPUT_FILE}")

if __name__ == "__main__":
    run_clustering()