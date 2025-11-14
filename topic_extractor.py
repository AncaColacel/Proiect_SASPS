import json
import re
import os
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation
import numpy as np

# --- 1. CONFIGURARE ---
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
    "spus", "dacă", "miliarde", "acolo", "aceste", "acestei", "însă", "avem"
]

# Lista de fișiere JSON de MODIFICAT (calea relativă la directorul Proiect_SASPS-andreea):
FILES_TO_PROCESS = [
    "collectors/digi24_ultimele_stiri_list.json",
    "collectors/hotNews_stiri_list.json",
    "collectors/antena1_stiri_list.json",
    "collectors/mediafax_stirile_zilei_list.json",
]


# --- 2. FUNCȚII ---

def load_data(file_path):
    """Încarcă datele din fișierul JSON."""
    try:
        # Folosim os.path.join pentru a construi calea corectă
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        print(f"EROARE: Fișierul nu a fost găsit la calea: {file_path}")
        return None

def save_data(data, file_path):
    """Salvează datele modificate înapoi în fișierul JSON."""
    try:
        # Folosim ensure_ascii=False și indent=4 pentru lizibilitate
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"[SUCCES] Fișierul a fost actualizat: {file_path}")
    except Exception as e:
        print(f"[EROARE] Nu s-a putut salva fișierul {file_path}: {e}")

def preprocess_text(text):
    """Curăță textul."""
    text = text.lower()
    text = re.sub(r'\d+', '', text)
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def assign_topics(data, n_topics=10, n_top_words=3):
    """
    Aplică modelul LDA, atribuie topicul dominant fiecărui articol
    și inserează rezultatul în structura JSON.
    """
    
    source_name = data.get('source', 'Sursă Necunoscută')
    documents = [article.get('content', '') for article in data.get('articles', [])]
    
    if not documents or all(doc == '' for doc in documents):
        print(f"[{source_name.upper()}] Nu s-a găsit conținut valid de procesat.")
        return data

    print(f"\n[{source_name.upper()}] -> Preprocesare: Curățarea a {len(documents)} documente...")
    processed_documents = [preprocess_text(doc) for doc in documents]

    # Vectorizare
    vectorizer = CountVectorizer(stop_words=ROMANIAN_STOP_WORDS, max_df=0.95, min_df=3)
    data_vectorized = vectorizer.fit_transform(processed_documents)
    feature_names = vectorizer.get_feature_names_out()
    
    print(f"[{source_name.upper()}] -> Vectorizare completă. S-au identificat {len(feature_names)} cuvinte unice.")

    # Modelare LDA
    lda_model = LatentDirichletAllocation(n_components=n_topics, max_iter=5, learning_method='online', random_state=42)
    lda_model.fit(data_vectorized)
    
    # Obținem probabilitățile de apartenență la topic pentru fiecare document
    doc_topic_dist = lda_model.transform(data_vectorized)
    # Atribuim ID-ul topicului dominant (cel cu probabilitatea cea mai mare)
    topic_ids = np.argmax(doc_topic_dist, axis=1)

    print(f"[{source_name.upper()}] -> Atribuire topicuri finalizată. Începe actualizarea JSON...")
    
    # Construim o hartă (map) cu Topic ID -> Cuvinte Cheie pentru afișare
    topic_keywords_map = {}
    for topic_idx, topic in enumerate(lda_model.components_):
        top_words = [feature_names[i] for i in topic.argsort()[:-n_top_words - 1:-1]]
        topic_keywords_map[topic_idx] = top_words

    # Actualizăm fiecare articol cu topicul atribuit
    for i, article in enumerate(data['articles']):
        assigned_id = int(topic_ids[i])
        keywords = topic_keywords_map.get(assigned_id, ['eroare', 'topic', 'necunoscut'])

        # Inserăm noul câmp 'topic' conform cerinței
        # Ex: "topic": {"id": 1, "keywords": ["rusia", "ucraina", "trump"]}
        article['topic'] = {
            'id': assigned_id + 1,  # Începem de la 1, nu de la 0, pentru lizibilitate
            'keywords': keywords
        }

    return data


# --- 3. RULARE PRINCIPALĂ ---

if __name__ == "__main__":
    
    print("Începe procesarea și actualizarea fișierelor JSON (Topic Tagging)...")
    
    for file_path in FILES_TO_PROCESS:
        
        print(f"\n{'#'*70}")
        print(f"# Procesare: {file_path}")
        print(f"{'#'*70}")

        # 1. Încărcare date
        data = load_data(file_path)
        
        if data is None:
            continue
        
        # 2. Atribuire Topicuri (Modifică structura datelor)
        data_modified = assign_topics(data)
        
        # 3. Salvare date modificate (Suprascrie fișierul original!)
        save_data(data_modified, file_path)

    print("\n[FINALIZAT] Toate fișierele JSON au fost actualizate cu topicuri!")