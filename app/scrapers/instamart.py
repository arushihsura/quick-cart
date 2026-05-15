from app.scrapers.base import BaseScraper, ScrapedProduct

class InstamartScraper(BaseScraper):

    def search_all(self, items: list) -> dict:
        print("[Instamart] Skipped — requires authenticated session")
        return {item: [] for item in items}
