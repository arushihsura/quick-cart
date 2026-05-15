from app.scrapers.base import BaseScraper


class BlinkitScraper(BaseScraper):
    def __init__(self, pincode: str = "400001"):
        super().__init__(pincode)
        self.app_name = "blinkit"