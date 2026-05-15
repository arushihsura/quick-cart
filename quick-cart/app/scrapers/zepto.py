from app.scrapers.base import BaseScraper


class ZeptoScraper(BaseScraper):
    def __init__(self, pincode: str = "400001"):
        super().__init__(pincode)
        self.app_name = "zepto"