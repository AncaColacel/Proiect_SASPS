# scraping/factory/base.py
from abc import ABC, abstractmethod


class Scraper(ABC):
    """Interfață comună pentru toți scrapers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Numele sursei (ex: 'hotnews', 'digi24')."""
        pass

    @abstractmethod
    def run(self) -> str:
        """
        Rulează scraping-ul pentru sursa respectivă și întoarce
        calea către fișierul JSON generat.
        """
        pass
