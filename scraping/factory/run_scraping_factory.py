# scraping/factory/run_scraping_factory.py
from .factory import ScraperFactory


def main():
    sources = ["hotnews", "digi24", "mediafax", "antena1"]

    print("🚀 Pornește scraping-ul folosind Factory Pattern...\n")

    generated_files = []

    for src in sources:
        scraper = ScraperFactory.create(src)
        print(f"=== Rulez scraper pentru {scraper.name} ===")
        json_file = scraper.run()
        generated_files.append(json_file)

    print("\n🎉 Scraping complet! Fișiere generate:")
    for f in generated_files:
        print(f" - {f}")


if __name__ == "__main__":
    main()
