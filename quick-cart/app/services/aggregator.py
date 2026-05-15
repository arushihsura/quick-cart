import asyncio
from concurrent.futures import ThreadPoolExecutor
from rapidfuzz import fuzz, process
from app.scrapers.blinkit import BlinkitScraper
from app.scrapers.zepto import ZeptoScraper
from app.scrapers.instamart import InstamartScraper

SCRAPERS = {
    "Blinkit": BlinkitScraper,
    "Zepto": ZeptoScraper,
    "Instamart": InstamartScraper,
}

def best_match(query: str, products: list):
    if not products:
        return None
    names = [p.name for p in products]
    match, score, idx = process.extractOne(query, names, scorer=fuzz.token_sort_ratio)
    print(f"[Match] '{query}' → '{match}' (score: {score})")
    if score > 55:
        return products[idx]
    return None

async def search_one_app(app_name: str, items: list[dict], pincode: str) -> dict:
    print(f"[Aggregator] Starting {app_name}...")
    try:
        scraper = SCRAPERS[app_name](pincode=pincode)
        cart = {}
        total = 0.0

        for item in items:
            print(f"[Aggregator] {app_name} searching: {item['item']}")
            try:
                results = await scraper.search(item["item"])
                print(f"[Aggregator] {app_name} got {len(results)} results for '{item['item']}'")
            except Exception as e:
                print(f"[Aggregator] {app_name} search EXCEPTION for '{item['item']}': {repr(e)}")
                results = []

            matched = best_match(item["item"], results)
            if matched:
                item_total = matched.price * item["quantity"]
                cart[item["item"]] = {
                    "product": matched.name,
                    "price": matched.price,
                    "quantity": item["quantity"],
                    "total": item_total,
                }
                total += item_total

        print(f"[Aggregator] {app_name} done. Total: ₹{total}")
        return {"app": app_name, "cart": cart, "total": total}

    except Exception as e:
        print(f"[Aggregator] {app_name} TOP-LEVEL EXCEPTION: {repr(e)}")
        import traceback
        traceback.print_exc()
        return None

async def compare_prices(items: list[dict], user_phone: str = None) -> list[dict]:
    print(f"[Aggregator] compare_prices called with {len(items)} items")
    tasks = [
        search_one_app(app, items, pincode="400001")
        for app in SCRAPERS
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    print(f"[Aggregator] Raw results: {results}")

    valid = [r for r in results if isinstance(r, dict) and r is not None]
    print(f"[Aggregator] Valid results: {len(valid)}")
    return sorted(valid, key=lambda x: x["total"])