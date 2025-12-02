import json
import re
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation

# --- CONFIGURARE ---
# Fișierul care ARE deja sentimente și entități
INPUT_FILE = "../jsons/final/baza_date_final_sentiments_entities.json" 
# Același fișier (sau unul nou) în care salvăm și topicurile
OUTPUT_FILE = "../jsons/final/baza_date_final_nlp.json"

# Stop words (cuvinte de legătură care nu ne interesează la topicuri)
ROMANIAN_STOP_WORDS = [
    "si", "sa", "un", "o", "ca", "pe", "cu", "la", "de", "din", "decat", "mai", "este", 
    "sunt", "se", "oameni", "acest", "acesta", "aceasta", "cei", "cel", "alea", 
    "fi", "fost", "lui", "ei", "ale", "pentru", "daca", "nu", "care", "cat", "avea",
    "a", "unui", "unei", "iar", "ori", "cum", "ce", "cand", "fata", "poate", 
    "dar", "va", "tot", "trebuie", "nici", "chiar", "doar", "asa", "deja", "fara",
    "şi", "că", "să", "ar", "al", "sau", "prin", "împotriva", "partea", "vor", "într",
    "era", "erau", "aveam", "aveau", "vom", "veți", "vor", "celor", "acestea",
    "ani", "românia", "declarat", "parte", "între", "mihai", "ioan", "setarile", "dat", 
    "trecut", "au", "el", "doi", "timp", "după", "privind", "această", "din", "am", "despre",
    "spus", "dacă", "miliarde", "acolo", "aceste", "acestei", "însă", "avem", "pentru", "fost"
]

def preprocess_text(text):
    """ Curăță textul pentru algoritmul LDA """
    text = text.lower()
    text = re.sub(r'\d+', '', text) # Fără cifre
    text = re.sub(r'[^\w\s]', '', text) # Fără punctuație
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def add_topics():
    print(f"📂 Încarc datele din '{INPUT_FILE}'...")
    try:
        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Standardizăm la listă dacă e doar un obiect
            if isinstance(data, dict): data = [data]
    except Exception as e:
        print(f"❌ Eroare la citire: {e}")
        return

    # --- ETAPA 1: COLECTARE TEXTE ---
    # Avem nevoie de toate textele deodată pentru a antrena modelul LDA
    all_docs = []
    articles_ref = [] # Păstrăm referința la obiectul articol ca să-l modificăm direct

    print("📝 Pregătesc textele pentru analiză...")
    for source in data:
        for article in source.get("articles", []):
            content = article.get("content", "")
            # Luăm în calcul doar articolele care au text consistent
            if content and len(content) > 50:
                all_docs.append(preprocess_text(content))
                articles_ref.append(article)

    if not all_docs:
        print("⚠️ Nu am găsit articole cu text valid.")
        return

    # --- ETAPA 2: VECTORIZARE & LDA ---
    print(f"🧠 Antrenez LDA pe {len(all_docs)} articole (poate dura puțin)...")
    
    # Transformăm textul în numere (Bag of Words)
    vectorizer = CountVectorizer(stop_words=ROMANIAN_STOP_WORDS, max_df=0.9, min_df=2)
    data_vectorized = vectorizer.fit_transform(all_docs)
    feature_names = vectorizer.get_feature_names_out()
    
    # Antrenăm modelul să găsească 5 topicuri dominante
    # Poți schimba n_components=10 dacă vrei teme mai specifice
    lda_model = LatentDirichletAllocation(n_components=5, max_iter=10, learning_method='online', random_state=42)
    lda_model.fit(data_vectorized)
    
    # Creăm o hartă: Topic ID -> Cuvinte Cheie
    topic_keywords_map = {}
    for topic_idx, topic in enumerate(lda_model.components_):
        # Luăm primele 4 cuvinte cheie pentru fiecare topic
        top_words = [feature_names[i] for i in topic.argsort()[:-5:-1]]
        topic_keywords_map[topic_idx] = top_words
        print(f"   🔹 Topic {topic_idx + 1}: {', '.join(top_words)}")

    # --- ETAPA 3: ATRIBUIRE TOPICURI ---
    print("📌 Atribui topicurile fiecărui articol...")
    
    # Calculăm distribuția pentru toate documentele
    doc_topic_dist = lda_model.transform(data_vectorized)

    # Iterează prin articole și adaugă câmpul "topic"
    for i, article in enumerate(articles_ref):
        # Găsim indexul topicului dominant
        topic_id = int(np.argmax(doc_topic_dist[i]))
        
        # Inserăm datele în articolul existent (păstrând sentiment/entities)
        article["topic"] = {
            "id": topic_id + 1,
            "keywords": topic_keywords_map.get(topic_id, [])
        }

    # --- ETAPA 4: SALVARE ---
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Gata! Fișierul '{OUTPUT_FILE}' are acum și topicuri.")

if __name__ == "__main__":
    add_topics()
