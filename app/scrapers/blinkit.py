from playwright.sync_api import sync_playwright
from app.scrapers.base import BaseScraper, ScrapedProduct
import httpx

class BlinkitScraper(BaseScraper):

    def _get_session(self):
        """Launch browser once to harvest live auth headers."""
        session = {}
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(extra_http_headers={
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                "Accept-Language": "en-IN,en;q=0.9",
            })
            page = context.new_page()

            def handle_response(response):
                if "v1/layout/search" in response.url and "offset" not in response.url:
                    if not session:
                        session.update(dict(response.request.headers))

            page.on("response", handle_response)
            page.goto("https://blinkit.com", timeout=20000)
            page.evaluate("""
                localStorage.setItem('gr_1_lat', '19.0760');
                localStorage.setItem('gr_1_lng', '72.8777');
            """)
            page.goto("https://blinkit.com/s/?q=Milk", timeout=20000)
            page.wait_for_load_state("networkidle", timeout=10000)
            browser.close()
        return session

    def _search_with_session(self, session: dict, item: str) -> list:
        headers = {k: v for k, v in session.items()}
        try:
            resp = httpx.get(
                "https://blinkit.com/v1/layout/search",
                headers=headers,
                params={"q": item, "search_type": "type_to_search"},
                timeout=10,
            )
            if resp.status_code != 200:
                print(f"[Blinkit] Status {resp.status_code} for '{item}'")
                return []

            data = resp.json()
            snippets = data.get("response", {}).get("snippets", [])
            results = []
            for s in snippets:
                d = s.get("data", {})
                name = d.get("name", {}).get("text")
                price_text = d.get("normal_price", {}).get("text", "")
                variant = d.get("variant", {}).get("text", "")
                inventory = d.get("inventory", 0)
                if not name or not price_text or inventory == 0:
                    continue
                try:
                    price = float(price_text.replace("₹", "").replace(",", "").strip())
                except:
                    continue
                results.append(ScrapedProduct(
                    name=name,
                    price=price,
                    quantity_str=variant,
                    available=True,
                    app="Blinkit"
                ))
            print(f"[Blinkit] '{item}' -> {len(results)} results")
            return results
        except Exception as e:
            print(f"[Blinkit] Error for '{item}': {repr(e)}")
            return []

    def search_all(self, items: list) -> dict:
        print("[Blinkit] Getting session...")
        session = self._get_session()
        if not session:
            print("[Blinkit] Failed to get session")
            return {item: [] for item in items}
        print("[Blinkit] Session obtained, searching items...")
        return {item: self._search_with_session(session, item) for item in items}
