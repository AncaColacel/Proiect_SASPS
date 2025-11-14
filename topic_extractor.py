import json
import re
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation
import os

# --- 1. CONFIGURARE ---
# Lista de cuvinte de oprire (Stop Words) în limba română - Lista finală optimizată
ROMANIAN_STOP_WORDS = [
    # Articole, Pronume, Conjuncții de bază
    "si", "sa", "un", "o", "ca", "pe", "cu", "la", "de", "din", "decat", "mai", "este", 
    "sunt", "se", "oameni", "acest", "acesta", "aceasta", "cei", "cel", "alea", 
    "fi", "fost", "lui", "ei", "ale", "pentru", "daca", "nu", "care", "cat", "avea",
    "a", "unui", "unei", "iar", "ori", "cum", "ce", "cand", "fata", "poate", 
    "dar", "va", "tot", "trebuie", "nici", "chiar", "doar", "asa", "deja", "fara",
    
    # Variante și forme frecvente
    "şi", "că", "să", "ar", "al", "sau", "prin", "împotriva", "partea", "vor", "într",
    "era", "erau", "aveam", "aveau", "vom", "veți", "vor", "celor", "acestea",
    
    # Cuvinte generice care au apărut în rezultat (final)
    "ani", "românia", "declarat", "parte", "între", "mihai", "ioan", "setarile", "dat", 
    "trecut", "au", "el", "doi", "timp", "după", "privind", "această", "din", "am", "despre",
    "spus", "dacă", "miliarde", "acolo", "aceste", "acestei", "însă", "avem"
]

# Lista de fișiere JSON de analizat:
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
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"EROARE: Fișierul nu a fost găsit la calea: {file_path}")
        return []

    content_list = [article.get('content', '') for article in data.get('articles', [])]
    return [content for content in content_list if content.strip()]

def preprocess_text(text):
    """Curăță textul."""
    text = text.lower()
    text = re.sub(r'\d+', '', text)
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def extract_topics(documents, source_name, n_topics=10, n_top_words=10):
    """Aplică modelul LDA și returnează rezultatele formatate."""
    
    print(f"\n[{source_name.upper()}] -> Preprocesare: Curățarea a {len(documents)} documente...")
    processed_documents = [preprocess_text(doc) for doc in documents]

    # Vectorizare cu min_df=3 pentru a ignora cuvintele foarte rare
    vectorizer = CountVectorizer(stop_words=ROMANIAN_STOP_WORDS, max_df=0.95, min_df=3)
    data_vectorized = vectorizer.fit_transform(processed_documents)
    feature_names = vectorizer.get_feature_names_out()

    print(f"[{source_name.upper()}] -> Vectorizare completă. S-au identificat {len(feature_names)} cuvinte unice.")

    lda_model = LatentDirichletAllocation(n_components=n_topics, max_iter=5, learning_method='online', random_state=42)
    lda_model.fit(data_vectorized)

    print(f"[{source_name.upper()}] -> Extragerea subiectelor finalizată.")
    
    # Construim textul rezultatelor
    results = []
    results.append("="*70)
    results.append(f"TOPICURI PRINCIPALE (LDA) pentru {source_name.upper()} ({len(documents)} articole)")
    results.append("="*70)
    
    for topic_idx, topic in enumerate(lda_model.components_):
        top_words = [feature_names[i] for i in topic.argsort()[:-n_top_words - 1:-1]]
        results.append(f"Subiectul #{topic_idx + 1}: {' '.join(top_words)}")
    results.append("="*70)
    
    return "\n".join(results)

def save_results(output_text, output_file):
    """Salvează textul rezultat într-un fișier."""
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(output_text)
        print(f"\n[SUCCES] Rezultatele au fost salvate în: {output_file}")
    except Exception as e:
        print(f"\n[EROARE] Nu s-a putut salva fișierul {output_file}: {e}")


# --- 3. RULARE PRINCIPALĂ ---

if __name__ == "__main__":
    
    # Iterăm prin fiecare fișier din lista FILES_TO_PROCESS
    for file_path in FILES_TO_PROCESS:
        
        # Extragem numele sursei din calea fișierului pentru a-l folosi la afișare/salvare
        # Ex: "collectors/digi24_ultimele_stiri_list.json" -> "digi24"
        source_name = os.path.basename(file_path).split('_')[0]
        output_file_name = f"topics_{source_name}.txt"
        
        print(f"\n{'#'*80}")
        print(f"# Începe analiza pentru {source_name.upper()} ({file_path})")
        print(f"{'#'*80}")
        
        # 1. Încărcare date
        documents = load_data(file_path)
        
        if not documents:
            print(f"Atenție: Nu s-a găsit conținut valid de procesat în {file_path}. Trecem la următorul fișier.")
            continue
        
        # 2. Extragere Topicuri
        output_text = extract_topics(documents, source_name)
        
        # 3. Afișare și Salvare
        print(output_text)
        save_results(output_text, output_file_name)