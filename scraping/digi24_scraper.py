from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin
import json
import time
from newspaper import Article
from datetime import datetime

BASE_URL = "https://www.digi24.ro"
LISTING_URL = f"{BASE_URL}/ultimele-stiri"

# 🔥 CONFIGURARE FILTRE
TARGET_CATEGORIES = ['politic', 'social', 'economic', 'externe', 'justitie', 'business']

# 🎲 SAMPLING (1 din 2 articole)
SAMPLE_RATE = 2

def fetch_listing_page(page: int = 1) -> str:
    """ Descarcă HTML cu Retry """
    if page == 1:
        url = LISTING_URL
    else:
        url = f"{LISTING_URL}?p={page}"

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
        
        # --- EXTRAGERE TAG-URI (Logica nouă bazată pe snippet-ul tău) ---
        # Căutăm containerul <ul class="tags-list">
        tags_ul = soup.find('ul', class_='tags-list')
        
        if tags_ul:
            # Căutăm link-urile specifice: <a class="tags-list-item-link">
            # Asta va ignora automat <li>Etichete:</li> care nu are link
            for link in tags_ul.find_all('a', class_='tags-list-item-link'):
                tag_text = link.get_text(strip=True)
                if tag_text:
                    tags_list.append(tag_text)
        
        # --- FALLBACK (Pentru articole foarte vechi care pot avea altă structură) ---
        if not tags_list:
            tags_div = soup.find('div', class_='tag') or soup.find('div', class_='tags')
            if tags_div:
                for link in tags_div.find_all('a'):
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

def collect_digi24_smart(start_date: datetime, end_date: datetime):
    all_articles = []
    page = 1
    keep_going = True
    page1_signature = None
    
    # Auto-Corecție Date
    if start_date > end_date:
        start_date, end_date = end_date, start_date
    if start_date.tzinfo: start_date = start_date.replace(tzinfo=None)
    if end_date.tzinfo: end_date = end_date.replace(tzinfo=None)

    print(f"🚀 START Scraping DIGI24: {start_date.date()} -> {end_date.date()}")

    while keep_going:
        html = fetch_listing_page(page)
        if not html: break

        soup = BeautifulSoup(html, "html.parser")
        article_items = soup.find_all('article', class_='article')
        
        if not article_items: 
            print("⛔ Nu sunt articole pe pagină. Stop.")
            break
            
        # Anti-Loop
        first_h2 = article_items[0].find('h2', class_='article-title')
        if first_h2 and first_h2.find('a'):
            check_href = first_h2.find('a')['href']
            check_url = urljoin(BASE_URL, check_href)
            if page == 1: page1_signature = check_url
            elif page > 1 and check_url == page1_signature:
                print(f"⛔ Loop detectat. Stop.")
                break

        print(f"📄 Pagina {page}: găsit {len(article_items)} articole raw. Filtrez...")

        def get_meta(article_tag):
            h2 = article_tag.find('h2', class_='article-title')
            if not h2: return None, None
            a = h2.find('a')
            if not a: return None, None
            return urljoin(BASE_URL, a['href']), a.get_text(strip=True)

        # Boundary Check
        u_url, u_title = get_meta(article_items[-1])
        if u_url:
            last_data = process_article(u_url, u_title)
            if last_data and last_data['date'] and last_data['date'] > end_date:
                print(f"⏩ SKIP Pagina {page} (prea nouă).")
                page += 1
                continue

        saved_count = 0
        for idx, art in enumerate(article_items):
            if idx % SAMPLE_RATE != 0: continue # Sampling

            url, title = get_meta(art)
            if not url: continue
            
            # Filtrare Categorie
            is_relevant = False
            for cat in TARGET_CATEGORIES:
                if cat in url: 
                    is_relevant = True
                    break
            if not is_relevant: continue

            art_data = process_article(url, title)
            if not art_data or not art_data['date']: continue
            
            curr_date = art_data['date']
            
            if start_date <= curr_date <= end_date:
                art_data['date'] = curr_date.isoformat()
                all_articles.append(art_data)
                tags_len = len(art_data.get('tags', []))
                print(f"   -> [{curr_date.date()}] {title[:30]}... | Tags: {tags_len}")
                saved_count += 1
            elif curr_date < start_date:
                print(f"🛑 Am ajuns în trecut ({curr_date.date()}). STOP.")
                keep_going = False
                break
        
        print(f"--- Pagina {page} gata. Salvate: {saved_count}")
        page += 1
        if page > 500: break

    return all_articles

if __name__ == "__main__":
    # Testează perioada dorită
    start = datetime(2025, 11, 26)
    end = datetime(2025, 1, 1)
    
    data = collect_digi24_smart(start, end)
    
    with open("../jsons/final/baza_date.json", "w", encoding="utf-8") as f:
        json.dump({"source": "Digi24", "count": len(data), "articles": data}, f, indent=2)
    print("🏁 Gata.")
