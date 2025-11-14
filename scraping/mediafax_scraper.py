from bs4 import BeautifulSoup
import requests
from dateutil import parser as date_parser
import json
import time
import newspaper


BASE_URL = "https://www.mediafax.ro"
LISTING_URL = f"{BASE_URL}/stirile-zilei"

def fetch_listing_page(page: int = 1) -> str:
    """
    Descarcă HTML pentru pagina din lista 'Știrile zilei'.
    page = 1 -> /stirile-zilei
    page > 1 -> /stirile-zilei/page/{page}
    """
    if page == 1:
        url = LISTING_URL
    else:
        url = f"{LISTING_URL}/page/{page}"

    response = requests.get(url, timeout=10)
    response.raise_for_status()
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
    
    articles_container = soup.find('div', class_ = 'articles xs:gap-15 gap-20')
    articles = articles_container.findAll('div', class_='article')

    articles_data = []

    for idx, article_div in enumerate(articles, start=1):
        # Extragem titlu + URL stire
        title_tag = article_div.find('h3', class_='article__title')
        if not title_tag:
            continue
        a_tag = title_tag.find('a')
        # print("a_tag ===========", a_tag)
        if not a_tag:
            continue

        title = a_tag.get_text(strip=True)
        url = a_tag['href']

        # aici intram direct pe articol, dand click pe link
        try:
            article_page = requests.get(url, timeout=10)
            article_page.raise_for_status()
            article_soup = BeautifulSoup(article_page.text, "html.parser")

            article = newspaper.Article(url)
            article.download(input_html=article_page.text)
            article.parse()
            
            tags = []
            tags_container = article_soup.find('div', class_='single__tags')
            if tags_container:
                tags = [a.get_text(strip=True) for a in tags_container.find_all('a')]

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

def collect_mediafax_stirile_zilei(max_pages: int = 1):
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
            # dacă o pagină nu mai are articole, ne oprim
            break

        all_articles.extend(page_articles)

    return {
        "source": "Mediafax",
        "source_url": BASE_URL,
        "section": "stirile-zilei",
        "pages_crawled": max_pages,
        "articles": all_articles
    }


if __name__ == "__main__":
    data = collect_mediafax_stirile_zilei(max_pages=4)

    with open("mediafax_stirile_zilei_list.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ Am salvat {len(data['articles'])} articole în mediafax_stirile_zilei_list.json")

