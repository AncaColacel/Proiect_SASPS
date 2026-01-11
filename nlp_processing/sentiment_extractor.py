import json
import torch
from torch.utils.data import Dataset
from transformers import pipeline
from transformers.pipelines.pt_utils import KeyDataset
from tqdm.auto import tqdm

# --- CONFIGURARE ---
import os
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
INPUT_FILE = os.path.join(DATA_DIR, "baza_date_final_with_entities.json")
OUTPUT_FILE = os.path.join(DATA_DIR, "baza_date_final_sentiments_entities.json")
MODEL_NAME = "readerbench/ro-sentiment"
BATCH_SIZE = 32  # Pe GPU T4 din Colab poți încerca și 64 sau 128

# Verificăm dacă avem GPU
device = 0 if torch.cuda.is_available() else -1
print(f"🖥️ Folosim device: {'GPU (cuda:0)' if device == 0 else 'CPU'}")

# --- 1. CLASA DATASET (Pentru a hrăni pipeline-ul eficient) ---
class NewsDataset(Dataset):
    def __init__(self, articles):
        self.articles = articles

    def __len__(self):
        return len(self.articles)

    def __getitem__(self, idx):
        # Returnăm doar textul pentru analiză
        content = self.articles[idx].get("content", "")
        # Fallback dacă e gol
        if not content or len(content) < 20:
            return "text gol" 
        return content

def process_sentiment_optimized():
    # 1. ÎNCĂRCARE DATELOR
    try:
        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"✅ Fișier încărcat: {INPUT_FILE}")
    except FileNotFoundError:
        print(f"❌ Nu am găsit fișierul: {INPUT_FILE}")
        return

    # 2. DETECTARE ȘI FLATTEN ARTICOLE
    # Acceptă atât listă plată de articole, cât și listă de surse cu "articles"
    all_articles_flat = []
    if isinstance(data, list):
        if data and isinstance(data[0], dict) and "content" in data[0]:
            # Flat list of articles
            all_articles_flat = data
        elif data and isinstance(data[0], dict) and "articles" in data[0]:
            # Nested: list of sources with "articles"
            for source in data:
                for article in source.get("articles", []):
                    # Optionally preserve source info if available
                    if "source" not in article and "source" in source:
                        article["source"] = source["source"]
                    all_articles_flat.append(article)
        else:
            print("❌ Structură de date necunoscută în input. Nicio acțiune efectuată.")
            return
    else:
        print("❌ Inputul nu este o listă. Nicio acțiune efectuată.")
        return

    total_articles = len(all_articles_flat)
    print(f"🚀 Pregătesc analiza pentru {total_articles} articole în batch-uri de {BATCH_SIZE}...")

    # 3. INITIALIZARE PIPELINE
    # Folosim batch_size în pipeline pentru viteză maximă
    classifier = pipeline(
        "text-classification",
        model=MODEL_NAME,
        tokenizer=MODEL_NAME,
        truncation=True,
        max_length=512,
        device=device,
        batch_size=BATCH_SIZE
    )

    # 4. DATASET WRAPPER
    dataset = NewsDataset(all_articles_flat)

    # 5. INFERENȚA ÎN BATCH (Aici e viteza!)
    # classifier(dataset) returnează un generator
    print("⏳ Rulez modelul pe GPU...")
    
    results = []
    # tqdm afișează bara de progres
    for out in tqdm(classifier(dataset), total=total_articles):
        results.append(out)

    # 6. MAPARE REZULTATE ÎNAPOI ÎN JSON
    print("💾 Salvez rezultatele...")
    for i, article in enumerate(all_articles_flat):
        res = results[i]
        raw_label = res['label']
        score = round(res['score'], 4)
        human_label = raw_label
        if raw_label == "LABEL_0": human_label = "negative"
        elif raw_label == "LABEL_1": human_label = "positive"
        elif raw_label == "LABEL_2": human_label = "neutral"
        if len(article.get("content", "")) < 20:
            human_label = "neutral"
            score = 0.0
        article["sentiment"] = {
            "label": human_label,
            "raw_label": raw_label,
            "score": score,
            "model": MODEL_NAME
        }

    # 7. SALVARE FINALĂ (mereu listă plată de articole)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_articles_flat, f, ensure_ascii=False, indent=2)
    print(f"\n🏁 Gata! Rezultatele sunt în '{OUTPUT_FILE}'.")

if __name__ == "__main__":
    process_sentiment_optimized()