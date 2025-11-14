from bs4 import BeautifulSoup
import requests
from dateutil import parser as date_parser
from urllib.parse import urljoin
import json
import time
import newspaper

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36'
}
BASE_URL = "https://www.digi24.ro/"
LISTING_URL = f"{BASE_URL}/ultimele-stiri"

def fetch_listing_page(page: int = 1) -> str:
    """
    Descarcă HTML pentru pagina din lista 'Știrile zilei'.
    page = 1 -> /ultimele-stiri
    page > 1 -> /ultimele-stiri?p={page}
    """
    if page == 1:
        url = LISTING_URL
    else:
        url = f"{LISTING_URL}?p={page}"

    response = requests.get(url, headers=HEADERS)
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
    
    articles_container = soup.find('div', class_ = 'col-10 col-md-12')
    articles = articles_container.findAll('article', class_='article brdr')

    articles_data = []

    for idx, article_div in enumerate(articles, start=1):
        # Extragem titlu + URL stire
        title_tag = article_div.find('h2', class_='article-title')
        if not title_tag:
            continue
        a_tag = title_tag.find('a')
        # print("a_tag ===========", a_tag)
        if not a_tag:
            continue

        relative_url = a_tag["href"]
        url = relative_url if relative_url.startswith("http") else urljoin(BASE_URL, relative_url)
        title = a_tag.get_text(strip=True)

        # aici intram direct pe articol, dand click pe link
        try:
            article_response = requests.get(url, headers=HEADERS)
            article_html = article_response.text
            article_soup = BeautifulSoup(article_html, "html.parser")

            tags_list = []
            tags_ul = article_soup.find('ul', class_='tags-list')
            if tags_ul:
                tags_li = tags_ul.find_all('li', class_='tags-list-item')
                for tag in tags_li:
                    tag_a = tag.find('a')
                    if tag_a:
                        tags_list.append(tag_a.get_text(strip=True))

            article = newspaper.Article(url)
            article.download(input_html=article_html)
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
            "tags": tags_list
        })

        time.sleep(1)
    
    return articles_data

def collect_digi24_ultimele_stiri(max_pages: int = 1):
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
        "source": "Digi24",
        "source_url": BASE_URL,
        "section": "stirile-zilei",
        "pages_crawled": max_pages,
        "articles": all_articles
    }


if __name__ == "__main__":
    data = collect_digi24_ultimele_stiri(max_pages=4)

    with open("digi24_ultimele_stiri_list.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ Am salvat {len(data['articles'])} articole în digi24_ultimele_stiri_list.json")

