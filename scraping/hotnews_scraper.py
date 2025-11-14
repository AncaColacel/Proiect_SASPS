from bs4 import BeautifulSoup
import requests
from dateutil import parser as date_parser
from urllib.parse import urljoin
import json
import time
import newspaper

BASE_URL = "https://hotnews.ro/"
LISTING_URL = f"{BASE_URL}/ultima-ora"

def fetch_listing_page(page: int = 1) -> str:
    """
    Descarcă HTML pentru pagina din lista 'Știrile zilei'.
    page = 1 -> /ultima-ora
    page > 1 -> /ultima-ora/page/{page}
    """
    if page == 1:
        url = LISTING_URL
    else:
        url = f"{LISTING_URL}/page/{page}"

    response = requests.get(url)
    return response.text

def parse_listing(html: str):
    """
    Primește HTML-ul unei pagini 'Știrile zilei' și extrage articolele.
    Returnează o listă de dict-uri cu:
      - title
      - url
      - time (ora afișată)
      - description
    """
    soup = BeautifulSoup(html, "html.parser")
    
    articles_container = soup.find('div', class_ = 'day-posts')

    if not articles_container:
        print("[WARN] Nu am găsit containerul de articole.")
        return []
    
    articles = articles_container.find_all('article', class_='ultima-ora')

    articles_data = []

    for idx, article_div in enumerate(articles, start=1):
        title_tag = article_div.find('h2', class_='entry-title')
        if not title_tag:
            continue

        a_tag = title_tag.find('a')
        if not a_tag:
            continue

        url = a_tag["href"]
        title = a_tag.get_text(strip=True)

        category_tag = article_div.find('div', class_='hn-category-tag')
        tags = []
        if category_tag:
            supratitlu_tag = category_tag.find('span', class_='supratitlu')
            if supratitlu_tag:
                tags.append(supratitlu_tag.get_text(strip=True))

        try:
            article = newspaper.Article(url)
            article.download()
            article.parse()
        except Exception as e:
            print(f"[WARN] Eroare la {url}: {e}")
            continue

        articles_data.append({
            "id": idx,
            "title": article.title or title,
            "url": url,
            "date": article.publish_date.date().isoformat() if article.publish_date else None,
            "content": article.text or "",
            "tags": tags
        })

        time.sleep(1)

    return articles_data

def collect_hot_news_stiri(max_pages: int = 1):
    """
    Colectează articole din primele `max_pages` pagini de la 'Știrile zilei'
    și le pune într-o structură JSON ușor de prelucrat ulterior.
    """
    all_articles = []

    for page in range(1, max_pages + 1):
        try:
            html = fetch_listing_page(page)
        except Exception as e:
            print(f"[WARN] Nu pot încărca pagina {page}: {e}")
            continue

        page_articles = parse_listing(html)
        if not page_articles:
            break

        all_articles.extend(page_articles)

    return {
        "source": "HotNews",
        "source_url": BASE_URL,
        "section": "news",
        "pages_crawled": max_pages,
        "articles": all_articles
    }

if __name__ == "__main__":
    data = collect_hot_news_stiri(max_pages=4)

    with open("hotNews_stiri_list.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ Am salvat {len(data['articles'])} articole în hotNews_stiri_list.json")