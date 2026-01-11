import os
import sys
import subprocess
import json

from datetime import datetime
from .base import Scraper
from scraping.hotnews_scraper import collect_hotnews_smart
from scraping.digi24_scraper import collect_digi24_smart
from scraping.mediafax_scraper import collect_mediafax_smart
from scraping.antena1_scraper import collect_antena1_stiri


CURRENT_FILE = os.path.abspath(__file__)

FACTORY_DIR = os.path.dirname(CURRENT_FILE)

SCRAPING_DIR = os.path.dirname(FACTORY_DIR)

PROJECT_ROOT = os.path.dirname(SCRAPING_DIR)

FACTORY_OUTPUT_DIR = os.path.join(PROJECT_ROOT, "jsons", "final", "factory")

# print(FACTORY_OUTPUT_DIR)

# Creăm folderul dacă nu există
os.makedirs(FACTORY_OUTPUT_DIR, exist_ok=True)

class HotNewsScraper(Scraper):
    @property
    def name(self) -> str:
        return "hotnews"

    def run(self) -> str:
        
        start = datetime(2025, 1, 20)
        end = datetime(2025, 1, 1)

        print(f"[HotNews/Factory] Colectez articole în intervalul {start.date()} - {end.date()} ...")
        new_articles = collect_hotnews_smart(start, end)

        if isinstance(new_articles, dict):
            articles_list = new_articles.get("articles", [])
        else:
            articles_list = new_articles

        print(f"[HotNews/Factory] Am colectat {len(articles_list)} articole.")

        final_json = {
            "source": "HotNews",
            "count": len(articles_list),
            "articles": articles_list,
        }

        out_path = os.path.join(FACTORY_OUTPUT_DIR, "baza_date_hotnews.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(final_json, f, ensure_ascii=False, indent=2)

        print(f"[HotNews/Factory] JSON salvat în: {out_path}")
        return out_path

class Digi24Scraper(Scraper):
    @property
    def name(self) -> str:
        return "digi24"

    def run(self) -> str:
        
        start = datetime(2025, 1, 20)
        end = datetime(2025, 1, 1)

        print(f"[Digi24/Factory] Colectez articole în intervalul {start.date()} - {end.date()} ...")
        new_articles = collect_digi24_smart(start, end)

        if isinstance(new_articles, dict):
            articles_list = new_articles.get("articles", [])
        else:
            articles_list = new_articles

        print(f"[Digi24/Factory] Am colectat {len(articles_list)} articole.")

        final_json = {
            "source": "Digi24",
            "count": len(articles_list),
            "articles": articles_list,
        }

        out_path = os.path.join(FACTORY_OUTPUT_DIR, "baza_date_digi.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(final_json, f, ensure_ascii=False, indent=2)

        print(f"[Digi24/Factory] JSON salvat în: {out_path}")
        return out_path



class MediafaxScraper(Scraper):
    @property
    def name(self) -> str:
        return "mediafax"

    def run(self) -> str:
        
        start = datetime(2025, 1, 20)
        end = datetime(2025, 1, 1)

        print(f"[Mediafax/Factory] Colectez articole în intervalul {start.date()} - {end.date()} ...")
        new_articles = collect_mediafax_smart(start, end)

        if isinstance(new_articles, dict):
            articles_list = new_articles.get("articles", [])
        else:
            articles_list = new_articles

        print(f"[Mediafax/Factory] Am colectat {len(articles_list)} articole.")

        final_json = {
            "source": "Mediafax",
            "count": len(articles_list),
            "articles": articles_list,
        }

        out_path = os.path.join(FACTORY_OUTPUT_DIR, "baza_date_mediafax.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(final_json, f, ensure_ascii=False, indent=2)

        print(f"[Mediafax/Factory] JSON salvat în: {out_path}")
        return out_path



class Antena1Scraper(Scraper):
    @property
    def name(self) -> str:
        return "antena1"

    def run(self) -> str:
        
        max_pages = 1  
        print(f"[Antena1/Factory] Colectez articole din primele {max_pages} pagini ...")
        data = collect_antena1_stiri(max_pages=max_pages)

        articles_list = data.get("articles", [])
        print(f"[Antena1/Factory] Am colectat {len(articles_list)} articole.")

        final_json = {
            "source": "Antena1",
            "count": len(articles_list),
            "articles": articles_list,
        }

        out_path = os.path.join(FACTORY_OUTPUT_DIR, "baza_date_antena.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(final_json, f, ensure_ascii=False, indent=2)

        print(f"[Antena1/Factory] JSON salvat în: {out_path}")
        return out_path
