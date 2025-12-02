from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin
import json
import time
import re
from newspaper import Article
from datetime import datetime

BASE_URL = "https://www.mediafax.ro"
LISTING_URL = f"{BASE_URL}/stirile-zilei"

# 🔥 CONFIGURARE FILTRE
# Scraperul va lua doar articolele care conțin aceste cuvinte în URL
TARGET_CATEGORIES = ['politic', 'social', 'economic', 'externe', 'business', 'sport']
# 🔥 CONFIGURARE SAMPLING
# 1 = Ia tot; 2 = Ia 1 din 2; 3 = Ia 1 din 3 (reduce volumul de 3 ori)
SAMPLE_RATE = 2 

def fetch_listing_page(page: int = 1) -> str:
    url = LISTING_URL if page == 1 else f"{LISTING_URL}/page/{page}"
    print(f"🔄 Request listing: {url}")
    try:
        response = requests.get(url, timeout=15)
        return response.text if response.status_code == 200 else ""
    except Exception as e:
        print(f"[ERR] {e}")
        return ""

def process_article(url, title):
    try:
        response = requests.get(url, timeout=15)
        if response.status_code != 200: return None
        html_content = response.text
        
        soup = BeautifulSoup(html_content, "html.parser")
        tags_list = []
        
        # Regex Tags
        script_tag = soup.find('script', id='uniqode_sync')
        if script_tag and script_tag.string:
            match = re.search(r"tags:\s*JSON\.parse\('([^']+)'\)", script_tag.string)
            if match:
                try:
                    tags_list = json.loads(match.group(1))
                except: pass
        
        # Fallback Tags
        if not tags_list:
            tags_container = soup.find('div', class_='labels') or soup.find('div', class_='tags')
            if tags_container:
                for tag_link in tags_container.find_all('a'):
                    tags_list.append(tag_link.get_text(strip=True))
        
        article = Article(url)
        article.download(input_html=html_content) 
        article.parse()
        
        pub_date = article.publish_date
        if pub_date and pub_date.tzinfo:
            pub_date = pub_date.replace(tzinfo=None)
            
        return {
            "title": article.title or title,
            "url": url,
            "date": pub_date,
            "content": article.text or "",
            "tags": tags_list
        }
    except Exception:
        return None

def collect_mediafax_smart(start_date: datetime, end_date: datetime):
    all_articles = []
    page = 500
    keep_going = True
    page1_signature = None
    
    # Auto-fix date
    if start_date > end_date:
        start_date, end_date = end_date, start_date
    if start_date.tzinfo: start_date = start_date.replace(tzinfo=None)
    if end_date.tzinfo: end_date = end_date.replace(tzinfo=None)

    print(f"🚀 START Scraping SMART: {start_date.date()} -> {end_date.date()}")
    print(f"🎯 Filtre active: {TARGET_CATEGORIES}")
    print(f"🎲 Sampling: 1 din {SAMPLE_RATE}")

    while keep_going:
        html = fetch_listing_page(page)
        if not html: break

        soup = BeautifulSoup(html, "html.parser")
        container = soup.find('div', class_='articles')
        if not container: break
        
        article_items = container.find_all('div', class_='article')
        if not article_items: break
            
        # Anti-Loop
        first_a = article_items[0].find('h3', class_='article__title').find('a')
        if first_a:
            check_url = urljoin(BASE_URL, first_a['href'])
            if page == 1: page1_signature = check_url
            elif page > 1 and check_url == page1_signature:
                print("⛔ Loop detectat. Stop.")
                break

        print(f"📄 Pagina {page}: găsit {len(article_items)} articole raw. Filtrez...")

        def get_meta(div):
            h3 = div.find('h3', class_='article__title')
            if not h3: return None, None
            a = h3.find('a')
            if not a: return None, None
            return urljoin(BASE_URL, a['href']), a.get_text(strip=True)

        # Boundary Check (doar pe ultimul, ca să sărim paginile noi rapid)
        u_url, u_title = get_meta(article_items[-1])
        if u_url:
            # Aici facem un request extra doar pentru verificare dată
            # Putem optimiza sărind verificarea de categorie pt boundary check
            last_data = process_article(u_url, u_title)
            if last_data and last_data['date'] and last_data['date'] > end_date:
                print(f"⏩ SKIP Pagina {page} (prea nouă).")
                page += 1
                continue

        # Procesare Articole
        saved_on_page = 0
        for idx, div in enumerate(article_items):
            # 🎲 1. SAMPLING: Luăm doar 1 din N articole
            if idx % SAMPLE_RATE != 0:
                continue

            url, title = get_meta(div)
            if not url: continue
            
            # 🛑 2. FILTRARE CATEGORIE (Fără request, doar din string URL)
            is_relevant = False
            for cat in TARGET_CATEGORIES:
                if f"/{cat}/" in url:
                    is_relevant = True
                    break
            
            if not is_relevant:
                # Putem ignora Sport, Life, Horoscope etc.
                continue

            # Dacă a trecut filtrele, procesăm greu (Request + Parsing)
            art_data = process_article(url, title)
            if not art_data or not art_data['date']: continue
            
            curr_date = art_data['date']
            
            if start_date <= curr_date <= end_date:
                art_data['date'] = curr_date.isoformat()
                all_articles.append(art_data)
                print(f"   -> [{curr_date.date()}] {title[:30]}...")
                saved_on_page += 1
            elif curr_date < start_date:
                print(f"🛑 Am ajuns în trecut ({curr_date.date()}). STOP.")
                keep_going = False
                break
        
        print(f"--- Pagina {page} gata. Relevante salvate: {saved_on_page}")
        page += 1
       

    return all_articles

import os

if __name__ == "__main__":
    # 1. SETARE PERIOADĂ
    start = datetime(2025, 6, 26) 
    end = datetime(2025, 1, 1)   
    
    # 2. RULARE SCRAPER (Obținem lista nouă de articole)
    new_articles = collect_mediafax_smart(start, end)
    
    # Calea fișierului
    output_path = "../jsons/final/baza_date_mediafax.json"
    
    # 3. PREGĂTIRE STRUCTURĂ
    final_json = {
        "source": "Mediafax",
        "count": 0,
        "articles": []
    }
    
    # 4. ÎNCĂRCARE DATE VECHI (Dacă fișierul există)
    if os.path.exists(output_path):
        try:
            with open(output_path, "r", encoding="utf-8") as f:
                loaded_data = json.load(f)
                # Verificăm dacă fișierul are structura corectă
                if isinstance(loaded_data, dict) and "articles" in loaded_data:
                    final_json = loaded_data
                    print(f"📂 Am încărcat baza existentă: {len(final_json['articles'])} articole.")
                else:
                    print("⚠️ Fișierul existent are o structură greșită. Îl voi suprascrie.")
        except Exception as e:
            print(f"⚠️ Eroare la citirea fișierului existent ({e}). Voi crea unul nou.")

    # 5. MERGE & DEDUPLICARE
    # Facem un set cu URL-urile deja existente pentru verificare rapidă
    existing_urls = {art['url'] for art in final_json['articles']}
    
    added_count = 0
    skipped_count = 0

    print("🔄 Combin datele noi cu cele vechi...")
    
    for item in new_articles:
        if item['url'] not in existing_urls:
            # Articolul e unic, îl adăugăm
            final_json['articles'].append(item)
            existing_urls.add(item['url']) # Îl adăugăm în set ca să nu-l mai băgăm o dată dacă apare duplicat în new_articles
            added_count += 1
        else:
            # Articolul există deja
            skipped_count += 1
            
    # Recalculăm totalul
    final_json['count'] = len(final_json['articles'])

    # 6. SALVARE FINALĂ
    try:
        # Ne asigurăm că folderul există
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(final_json, f, ensure_ascii=False, indent=2)
            
        print(f"💾 SALVARE REUȘITĂ în {output_path}")
        print(f"   ➕ Noi adăugate: {added_count}")
        print(f"   ⏭️ Duplicate ignorate: {skipped_count}")
        print(f"   📚 TOTAL în bază: {final_json['count']}")
        
    except Exception as e:
        print(f"❌ Eroare critică la salvare: {e}")
