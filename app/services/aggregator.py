import asyncio
from concurrent.futures import ProcessPoolExecutor
from rapidfuzz import fuzz, process

def best_match(query: str, products: list):
    if not products:
        return None
    query_lower = query.lower().strip()
    names = [p['name'] for p in products]

    for i, name in enumerate(names):
        if query_lower in name.lower():
            print(f"[Match] '{query}' -> '{name}' (substring)")
            return products[i]

    match, score, idx = process.extractOne(query, names, scorer=fuzz.partial_ratio)
    print(f"[Match] '{query}' -> '{match}' (partial_ratio: {score})")
    if score >= 60:
        return products[idx]

    match, score, idx = process.extractOne(query, names, scorer=fuzz.token_set_ratio)
    print(f"[Match] '{query}' -> '{match}' (token_set_ratio: {score})")
    if score >= 70:
        return products[idx]

    return None

def _run_blinkit(item_names: list) -> dict:
    from playwright.sync_api import sync_playwright

    results = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(extra_http_headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept-Language": "en-IN,en;q=0.9",
        })
        page = context.new_page()

        # Set location
        page.goto("https://blinkit.com", timeout=20000)
        page.evaluate("""
            localStorage.setItem('gr_1_lat', '19.0760');
            localStorage.setItem('gr_1_lng', '72.8777');
        """)

        for item in item_names:
            items_out = []
            search_done = [False]

            def handle(response, item=item):
                if "v1/layout/search" in response.url and "offset" not in response.url:
                    try:
                        data = response.json()
                        snippets = data.get("response", {}).get("snippets", [])
                        for s in snippets:
                            d = s.get("data", {})
                            name = d.get("name", {}).get("text")
                            price_text = d.get("normal_price", {}).get("text", "")
                            variant = d.get("variant", {}).get("text", "")
                            if not name or not price_text or d.get("inventory", 0) == 0:
                                continue
                            try:
                                price = float(price_text.replace("₹","").replace(",","").strip())
                                items_out.append({"name": name, "price": price, "quantity_str": variant})
                            except:
                                continue
                        search_done[0] = True
                    except:
                        pass

            page.on("response", handle)
            page.goto(f"https://blinkit.com/s/?q={item.replace(' ', '+')}", timeout=20000)
            page.wait_for_load_state("networkidle", timeout=10000)
            page.remove_listener("response", handle)

            print(f"[Blinkit] '{item}' -> {len(items_out)} results")
            results[item] = items_out

        browser.close()
    return results

def _run_zepto(item_names: list) -> dict:
    from playwright.sync_api import sync_playwright
    import httpx
    import uuid

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

        def handle(response):
            if "user-search-service/api/v3/search" in response.url and "filters" not in response.url:
                if "SHOW_ALL_RESULTS" in (response.request.post_data or "") and not session:
                    session.update(dict(response.request.headers))

        page.on("response", handle)
        page.goto("https://www.zepto.com", timeout=30000)
        page.wait_for_load_state("networkidle", timeout=10000)
        page.wait_for_timeout(2000)
        page.goto("https://www.zepto.com/search?query=Milk", timeout=30000)
        page.wait_for_load_state("networkidle", timeout=10000)
        page.wait_for_timeout(2000)
        browser.close()

    if not session:
        print("[Zepto] No session captured")
        return {item: [] for item in item_names}

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

    results = {}
    for item in item_names:
        try:
            resp = httpx.post(
                "https://bff-gateway.zepto.com/user-search-service/api/v3/search",
                headers=headers,
                json={"query": item, "pageNumber": 0, "mode": "SHOW_ALL_RESULTS", "userSessionId": str(uuid.uuid4())},
                timeout=10,
            )
            items_out = []
            for widget in resp.json().get("layout", []):
                for i in widget.get("data", {}).get("resolver", {}).get("data", {}).get("items", []):
                    pr = i.get("productResponse", {})
                    name = pr.get("product", {}).get("name", "")
                    packsize = pr.get("productVariant", {}).get("formattedPacksize", "")
                    price_raw = pr.get("discountedSellingPrice", 0)
                    if not name or not price_raw or pr.get("outOfStock", True):
                        continue
                    items_out.append({"name": name, "price": price_raw / 100, "quantity_str": packsize})
            print(f"[Zepto] '{item}' -> {len(items_out)} results")
            results[item] = items_out
        except Exception as e:
            print(f"[Zepto] Error '{item}': {repr(e)}")
            results[item] = []
    return results

def _build_cart(items: list, all_results: dict, app_name: str) -> dict:
    cart = {}
    total = 0.0
    for item in items:
        results = all_results.get(item["item"], [])
        matched = best_match(item["item"], results)
        if matched:
            item_total = matched["price"] * item["quantity"]
            cart[item["item"]] = {
                "product": matched["name"],
                "price": matched["price"],
                "quantity": item["quantity"],
                "total": item_total,
            }
            total += item_total
    return {"app": app_name, "cart": cart, "total": total}

async def compare_prices(items: list, user_phone: str = None) -> list:
    print(f"[Aggregator] Comparing prices for {len(items)} items...")
    item_names = [i["item"] for i in items]
    loop = asyncio.get_event_loop()

    with ProcessPoolExecutor(max_workers=2) as pool:
        blinkit_results, zepto_results = await asyncio.gather(
            loop.run_in_executor(pool, _run_blinkit, item_names),
            loop.run_in_executor(pool, _run_zepto, item_names),
            return_exceptions=True
        )

    final = []
    for app_name, results in [("Blinkit", blinkit_results), ("Zepto", zepto_results)]:
        if isinstance(results, dict):
            final.append(_build_cart(items, results, app_name))
        else:
            print(f"[{app_name}] Failed: {repr(results)}")

    print(f"[Aggregator] Results: {final}")
    return sorted(final, key=lambda x: x["total"])
