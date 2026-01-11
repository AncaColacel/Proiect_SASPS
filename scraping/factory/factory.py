# scraping/factory/factory.py
from .scrapers import (
    HotNewsScraper,
    Digi24Scraper,
    MediafaxScraper,
    Antena1Scraper,
)
from .base import Scraper


class ScraperFactory:
    """Factory pentru crearea scraperului corect în funcție de nume."""

    registry = {
        "hotnews": HotNewsScraper,
        "digi24": Digi24Scraper,
        "mediafax": MediafaxScraper,
        "antena1": Antena1Scraper,
    }

    @classmethod
    def create(cls, source: str) -> Scraper:
        source = source.lower()
        if source not in cls.registry:
            raise ValueError(f"Sursa '{source}' nu este suportată.")
        return cls.registry[source]()
