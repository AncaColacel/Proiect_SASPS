from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin
import json
import time
from newspaper import Article
from datetime import datetime

BASE_URL = "https://hotnews.ro"
LISTING_URL = f"{BASE_URL}/ultima-ora"

# 🎲 SAMPLING (1 din 2 articole)
SAMPLE_RATE = 2 
# 🛡️ BUFFER DE SIGURANȚĂ (Câte articole vechi consecutive acceptăm înainte de STOP)
OLD_ARTICLES_THRESHOLD = 3 

def fetch_listing_page(page: int = 1) -> str:
    """ Descarcă HTML cu Retry (3 încercări) """
    if page == 1:
        url = LISTING_URL
    else:
        url = f"{LISTING_URL}/page/{page}"

    print(f"🔄 Request listing: {url}")
    
    retries = 3
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=15)
            if response.status_code == 200:
                return response.text
            elif response.status_code == 404:
                return ""
            time.sleep(2)
        except Exception as e:
            print(f"⚠️ Eroare conexiune: {e}. Retry {attempt+1}...")
            time.sleep(3)
    return ""

def process_article(url, title):
    try:
        # 1. HTML Request
        response = requests.get(url, timeout=15)
        if response.status_code != 200: return None
        html_content = response.text
        
        soup = BeautifulSoup(html_content, "html.parser")
        tags_list = []
        
        # --- EXTRAGERE TAG-URI (META tags) ---
        meta_tag = soup.find('meta', attrs={'name': 'parsely-tags'})
        
        if meta_tag and meta_tag.get('content'):
            raw_tags = meta_tag['content'].split(',')
            tags_list = [t.strip() for t in raw_tags if t.strip()]
        
        # Fallback div
        if not tags_list:
            tags_container = soup.find('div', class_='post-tags') or soup.find('div', class_='tags')
            if tags_container:
                for link in tags_container.find_all('a'):
                    tags_list.append(link.get_text(strip=True))
        
        # 2. Newspaper3k
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

def collect_hotnews_smart(start_date: datetime, end_date: datetime, max_articles=50):
    all_articles = []
    page = 500
    keep_going = True
    page1_signature = None
    
    # Auto-Corecție Date
    if start_date > end_date:
        print("⚠️ Datele erau inversate. Le-am corectat automat (Start <-> End).")
        start_date, end_date = end_date, start_date
        
    if start_date.tzinfo: start_date = start_date.replace(tzinfo=None)
    if end_date.tzinfo: end_date = end_date.replace(tzinfo=None)

    print(f"🚀 START Scraping HotNews: {start_date.date()} -> {end_date.date()}")

    while keep_going:
        html = fetch_listing_page(page)
        if not html: break

        soup = BeautifulSoup(html, "html.parser")
        
        container = soup.find('div', class_='day-posts')
        if not container:
            print("⛔ Nu am găsit containerul 'day-posts'. Stop.")
            break
            
        article_items = container.find_all('article', class_='ultima-ora')
        if not article_items: 
            print("⛔ Nu sunt articole pe pagină. Stop.")
            break
            
        # --- ANTI-LOOP ---
        first_h2 = article_items[0].find('h2', class_='entry-title')
        if first_h2 and first_h2.find('a'):
            check_href = first_h2.find('a')['href']
            check_url = check_href if check_href.startswith("http") else urljoin(BASE_URL, check_href)

            if page == 1:
                page1_signature = check_url
                print(f"📌 Amprenta Pagina 1 memorată.")
            elif page > 1 and check_url == page1_signature:
                print(f"⛔ LOOP DETECTAT LA PAGINA {page}! (Redirect la Home). Stop.")
                break

        print(f"📄 Pagina {page}: găsit {len(article_items)} articole raw. Procesez...")

        def get_meta(article_tag):
            h2 = article_tag.find('h2', class_='entry-title')
            if not h2: return None, None
            a = h2.find('a')
            if not a: return None, None
            href = a['href']
            full_url = href if href.startswith("http") else urljoin(BASE_URL, href)
            return full_url, a.get_text(strip=True)

        # Boundary Check (SKIP la cele prea noi)
        u_url, u_title = get_meta(article_items[-1])
        if u_url:
            last_data = process_article(u_url, u_title)
            if last_data and last_data['date'] and last_data['date'] > end_date:
                print(f"⏩ SKIP Pagina {page} (prea nouă: {last_data['date'].date()}).")
                page += 1
                continue

        saved_count = 0
        # Variabilă pentru a număra câte articole vechi consecutive găsim
        consecutive_old_counter = 0 

        for idx, art in enumerate(article_items):
            if len(all_articles) >= max_articles:
                keep_going = False
                break
            # Sampling
            if idx % SAMPLE_RATE != 0: continue

            url, title = get_meta(art)
            if not url: continue
            
            art_data = process_article(url, title)
            if not art_data or not art_data['date']: continue
            
            curr_date = art_data['date']
            
            # --- LOGICA NOUĂ DE FILTRARE ---
            
            # CAZ 1: Articolul este bun (în interval)
            if start_date <= curr_date <= end_date:
                art_data['date'] = curr_date.isoformat()
                all_articles.append(art_data)
                tags_len = len(art_data.get('tags', []))
                print(f"   -> [{curr_date.date()}] {title[:30]}... | Tags: {tags_len}")
                saved_count += 1
                # RESETĂM contorul dacă dăm de un articol bun!
                consecutive_old_counter = 0 

            # CAZ 2: Articolul este prea vechi (< start)
            elif curr_date < start_date:
                consecutive_old_counter += 1
                print(f"   ⚠️ Articol vechi detectat ({curr_date.date()}). Verificare siguranță: {consecutive_old_counter}/{OLD_ARTICLES_THRESHOLD}")
                
                # Doar dacă am găsit 3 (sau valoarea setată) la rând ne oprim
                if consecutive_old_counter >= OLD_ARTICLES_THRESHOLD:
                    print(f"🛑 Am găsit {OLD_ARTICLES_THRESHOLD} articole consecutive vechi. STOP DEFINITIV.")
                    keep_going = False
                    break
            
            # CAZ 3: Articolul este prea nou (> end) - Îl ignorăm, dar nu resetăm neapărat contorul de vechime
            else:
                 pass 

        
        print(f"--- Pagina {page} gata. Salvate: {saved_count}")
        page += 1
        
       

    return all_articles

import os
import json
from datetime import datetime

# ... (funcțiile tale de scraping rămân neschimbate) ...

if __name__ == "__main__":
    # 1. RULARE SCRAPER (Datele Noi)
    # Setează aici noua perioadă pe care vrei să o adaugi
    start = datetime(2025, 3, 26) 
    end = datetime(2025, 1, 1)    
    
    # Colectăm datele noi folosind funcția ta
    new_data_raw = collect_hotnews_smart(start, end)
    
    # Verificăm ce returnează funcția ta (listă sau dict)
    if isinstance(new_data_raw, dict):
        new_articles = new_data_raw.get("articles", [])
    else:
        new_articles = new_data_raw # E deja listă

    # Calea către fișierul tău
    output_path = "../jsons/final/baza_date_hotnews.json"
    
    # 2. ÎNCĂRCARE DATE VECHI (Dacă există)
    final_json = {
        "source": "HotNews", 
        "count": 0, 
        "articles": []
    }
    
    if os.path.exists(output_path):
        try:
            with open(output_path, "r", encoding="utf-8") as f:
                existing_content = json.load(f)
                # Păstrăm structura existentă
                final_json = existing_content
                print(f"📂 Am încărcat baza de date existentă: {len(final_json['articles'])} articole.")
        except Exception as e:
            print(f"⚠️ Fișierul există dar e corupt sau gol, voi crea unul nou. ({e})")

    # 3. MERGE & DEDUPLICARE
    # Folosim un Set cu URL-uri pentru a detecta rapid duplicatele
    existing_urls = {art['url'] for art in final_json['articles']}
    
    added_count = 0
    skipped_count = 0

    print("🔄 Combin datele noi cu cele vechi...")
    
    for item in new_articles:
        if item['url'] not in existing_urls:
            # E un articol nou, îl adăugăm
            final_json['articles'].append(item)
            existing_urls.add(item['url']) # Îl marcăm ca văzut
            added_count += 1
        else:
            # E duplicat, îl ignorăm
            skipped_count += 1
            
    # Actualizăm numărătoarea totală
    final_json['count'] = len(final_json['articles'])

    # 4. SALVARE FINALĂ (Suprascriere cu lista completă)
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(final_json, f, ensure_ascii=False, indent=2)
            
        print(f"💾 SALVARE REUȘITĂ!")
        print(f"   ➕ Noi adăugate: {added_count}")
        print(f"   ⏭️ Duplicate ignorate: {skipped_count}")
        print(f"   📚 TOTAL în bază: {final_json['count']}")
        
    except Exception as e:
        print(f"❌ Eroare critică la salvare: {e}")
