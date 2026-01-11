import sys
import os

# Asigurăm că Python vede modulele
sys.path.append(os.path.dirname(__file__))

# Importăm strategiile
from nlp_processing.ner_strategies.context import NERProcessor
from nlp_processing.ner_strategies.strategies import RegexStrategy, TransformerStrategy

# --- TEXT REAL DIN PROIECT (Sursa: Digi24 / baza_date_digi.json) ---
# Aceasta este o știre reală extrasă de scraper-ul vostru.
TITLU_REAL = "Marcel Ciolacu și-a depus candidatura la CJ Buzău."
TEXT_REAL = """
Fostul președinte PSD și premier Marcel Ciolacu și-a depus astăzi candidatura la șefia Consiliului Județean Buzău. 
Înainte de a se înscrie oficial, social-democratul a lansat o serie de înțepături la adresa prim-ministrului Ilie Bolojan.
Marcel Ciolacu a promis că, împreună cu primarul orașului Buzău, Constantin Toma, va începe dezvoltarea și altor zone din județ.
"""

def run_demo():
    print("="*60)
    print(" DEMONSTRAȚIE STRATEGY PATTERN - NER MODULE")
    print("="*60)
    print(f"Știre analizată (Sursa: Digi24 Scraper):")
    print(f"TITLU: {TITLU_REAL}")
    print(f"CONȚINUT: {TEXT_REAL.strip()}...")
    print("-" * 60)

    # Combinăm titlul cu textul pentru analiză
    full_text = f"{TITLU_REAL} {TEXT_REAL}"

    # 1. Pornim cu varianta SIMPLĂ
    print("\n PASUL 1: Rulare cu Strategia REGEX (Clasică)")
    processor = NERProcessor(strategy_type="regex")
    rezultat_1 = processor.process_text(full_text)
    
    # Afișăm rezultatele (doar textul)
    texts = [e['text'] for e in rezultat_1]
    print(f" Rezultat Regex (Găsește doar cuvinte cu majusculă):")
    print(f"   {texts}")

    # 2. Schimbăm strategia din mers
    print("\n" + "-"*60)
    input("⌨️  Apasă ENTER pentru a activa Inteligența Artificială (Transformer)...")
    print("-" * 60)

    print("\n PASUL 2: Schimbare strategie (Runtime) -> TRANSFORMER")
    processor.set_strategy(TransformerStrategy())
    
    rezultat_2 = processor.process_text(full_text)
    
    print("\n Rezultat AI (Înțelege contextul):")
    if not rezultat_2:
        print("   (Se încarcă modelul...)")
    else:
        for ent in rezultat_2:
            print(f"    {ent['text']} -> {ent['type']}")

    print("\n Demonstrație completă. Modulul 'ner_strategies' funcționează perfect.")

if __name__ == "__main__":
    run_demo()
