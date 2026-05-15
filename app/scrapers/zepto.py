from playwright.sync_api import sync_playwright
from app.scrapers.base import BaseScraper, ScrapedProduct
import httpx
import json
import uuid

class ZeptoScraper(BaseScraper):

    def _get_session(self):
        session = {}
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                locale="en-IN",
                timezone_id="Asia/Kolkata",
                viewport={"width": 1280, "height": 720},
            )
            page = context.new_page()
            page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                window.chrome = {runtime: {}};
            """)

            def handle_response(response):
                if "user-search-service/api/v3/search" in response.url and "filters" not in response.url:
                    if "SHOW_ALL_RESULTS" in (response.request.post_data or ""):
                        if not session:
                            session.update(dict(response.request.headers))

            page.on("response", handle_response)
            page.goto("https://www.zepto.com", timeout=30000)
            page.wait_for_load_state("networkidle", timeout=10000)
            page.wait_for_timeout(2000)
            page.goto("https://www.zepto.com/search?query=Milk", timeout=30000)
            page.wait_for_load_state("networkidle", timeout=10000)
            page.wait_for_timeout(2000)
            browser.close()
        return session

    def _search_with_session(self, session: dict, item: str) -> list:
        headers = {
            "content-type": "application/json",
            "user-agent": session.get("user-agent", ""),
            "accept-language": "en-IN,en;q=0.9",
            "x-xsrf-token": session.get("x-xsrf-token", ""),
            "x-csrf-secret": session.get("x-csrf-secret", ""),
            "storeid": session.get("storeid", ""),
            "store_id": session.get("store_id", ""),
            "store_ids": session.get("store_ids", ""),
            "sessionid": session.get("sessionid", ""),
            "session_id": session.get("session_id", ""),
            "deviceid": session.get("deviceid", ""),
            "device_id": session.get("device_id", ""),
            "appversion": session.get("appversion", "15.21.1"),
            "app_version": session.get("app_version", "15.21.1"),
            "tenant": "ZEPTO",
            "platform": "WEB",
            "app_sub_platform": "WEB",
            "source": "DIRECT",
            "marketplace_type": "SUPER_SAVER",
            "auth_revamp_flow": "v2",
            "referer": "https://www.zepto.com/",
        }
        payload = {
            "query": item,
            "pageNumber": 0,
            "mode": "SHOW_ALL_RESULTS",
            "userSessionId": str(uuid.uuid4()),
        }
        try:
            resp = httpx.post(
                "https://bff-gateway.zepto.com/user-search-service/api/v3/search",
                headers=headers,
                json=payload,
                timeout=10,
            )
            data = resp.json()
            layout = data.get("layout", [])
            results = []
            for widget in layout:
                items = widget.get("data", {}).get("resolver", {}).get("data", {}).get("items", [])
                for item_data in items:
                    pr = item_data.get("productResponse", {})
                    name = pr.get("product", {}).get("name", "")
                    packsize = pr.get("productVariant", {}).get("formattedPacksize", "")
                    selling_price = pr.get("discountedSellingPrice", 0)
                    out_of_stock = pr.get("outOfStock", True)
                    if not name or not selling_price or out_of_stock:
                        continue
                    price = selling_price / 100
                    results.append(ScrapedProduct(
                        name=name,
                        price=price,
                        quantity_str=packsize,
                        available=True,
                        app="Zepto"
                    ))
            print(f"[Zepto] '{item}' -> {len(results)} results")
            return results
        except Exception as e:
            print(f"[Zepto] API error for '{item}': {repr(e)}")
            return []

    def search_all(self, items: list) -> dict:
        print("[Zepto] Getting session...")
        session = self._get_session()
        if not session:
            print("[Zepto] Failed to get session")
            return {item: [] for item in items}
        print("[Zepto] Session obtained, searching items...")
        return {item: self._search_with_session(session, item) for item in items}
