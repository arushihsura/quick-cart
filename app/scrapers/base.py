import asyncio
import json
import sys
from abc import ABC
from dataclasses import dataclass
from pathlib import Path


WORKER_PATH = Path(__file__).with_name("worker.py")


@dataclass
class ScrapedProduct:
    name: str
    price: float
    quantity_str: str
    available: bool
    app: str


async def run_scraper_subprocess(app_name: str, item: str, pincode: str = "400001") -> list[ScrapedProduct]:
    payload = json.dumps({"app": app_name, "item": item, "pincode": pincode})

    try:
        proc = await asyncio.create_subprocess_exec(
            sys.executable,
            str(WORKER_PATH),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(input=payload.encode("utf-8")),
            timeout=30.0,
        )

        if stderr:
            print(stderr.decode("utf-8", errors="replace"), end="")

        raw = stdout.decode("utf-8", errors="replace").strip()
        if not raw:
            return []

        data = json.loads(raw)
        products: list[ScrapedProduct] = []
        for entry in data:
            if not isinstance(entry, dict):
                continue
            product_data = dict(entry)
            product_data.setdefault("app", app_name)
            products.append(ScrapedProduct(**product_data))
        return products

    except asyncio.TimeoutError:
        print(f"[{app_name}] Subprocess timed out")
        return []
    except Exception as e:
        print(f"[{app_name}] Subprocess error: {repr(e)}")
        return []


class BaseScraper(ABC):
    def __init__(self, pincode: str = "400001"):
        self.pincode = pincode
        self.app_name = ""

    async def search(self, item: str) -> list[ScrapedProduct]:
        return await run_scraper_subprocess(self.app_name, item, self.pincode)