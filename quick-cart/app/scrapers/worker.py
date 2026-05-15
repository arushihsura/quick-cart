"""
Standalone scraper worker. Run as a subprocess.
Receives JSON on stdin: {"app": "blinkit", "item": "Milk", "pincode": "400001"}
Returns JSON on stdout: []
"""

import json
import sys

from playwright.sync_api import sync_playwright


STEALTH_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "en-IN,en;q=0.9",
}


def scrape_blinkit(item: str, pincode: str) -> list[dict]:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(extra_http_headers=STEALTH_HEADERS)
        page = context.new_page()
        try:
            page.goto("https://blinkit.com", timeout=20000)
            page.evaluate(
                """
                localStorage.setItem('gr_1_lat', '19.0760');
                localStorage.setItem('gr_1_lng', '72.8777');
                """
            )
            page.goto(f"https://blinkit.com/s/?q={item.replace(' ', '+')}", timeout=20000)
            page.wait_for_load_state("networkidle", timeout=10000)
            title = page.title()
            print(f"[Blinkit worker] title: {title}", file=sys.stderr)
            return []
        except Exception as e:
            print(f"[Blinkit worker] error: {repr(e)}", file=sys.stderr)
            return []
        finally:
            browser.close()


def scrape_zepto(item: str, pincode: str) -> list[dict]:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(extra_http_headers=STEALTH_HEADERS)
        page = context.new_page()
        try:
            page.goto("https://www.zeptonow.com", timeout=20000)
            page.wait_for_load_state("networkidle", timeout=10000)
            title = page.title()
            print(f"[Zepto worker] title: {title}", file=sys.stderr)
            return []
        except Exception as e:
            print(f"[Zepto worker] error: {repr(e)}", file=sys.stderr)
            return []
        finally:
            browser.close()


def scrape_instamart(item: str, pincode: str) -> list[dict]:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(extra_http_headers=STEALTH_HEADERS)
        page = context.new_page()
        try:
            page.goto("https://www.swiggy.com/instamart", timeout=20000)
            page.wait_for_load_state("networkidle", timeout=10000)
            title = page.title()
            print(f"[Instamart worker] title: {title}", file=sys.stderr)
            return []
        except Exception as e:
            print(f"[Instamart worker] error: {repr(e)}", file=sys.stderr)
            return []
        finally:
            browser.close()


SCRAPERS = {
    "blinkit": scrape_blinkit,
    "zepto": scrape_zepto,
    "instamart": scrape_instamart,
}


if __name__ == "__main__":
    payload = json.loads(sys.stdin.read() or "{}")
    app = str(payload.get("app", "")).lower()
    item = payload.get("item", "")
    pincode = payload.get("pincode", "400001")

    scraper_fn = SCRAPERS.get(app)
    if not scraper_fn:
        print(json.dumps([]))
        sys.exit(1)

    results = scraper_fn(item, pincode)
    print(json.dumps(results))