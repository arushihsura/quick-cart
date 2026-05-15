import google.generativeai as genai
import json
import os
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")

SYSTEM_PROMPT = """
You are a grocery list parser for an Indian quick-commerce app.
Extract all grocery items from the user's message.
Normalize item names to common Indian grocery terms.
Infer quantities if not stated (default to 1).
Return ONLY a JSON array. No explanation, no markdown.
Format:
[{"item": "Amul Milk", "quantity": 2, "unit": "litre"}]
If no groceries found, return []
"""

async def extract_grocery_list(user_message: str) -> list[dict]:
    print(f"[Gemini] Parsing message: '{user_message}'")
    try:
        response = model.generate_content(
            f"{SYSTEM_PROMPT}\n\nUser message:\n{user_message}"
        )
        raw = response.text.strip()
        print(f"[Gemini] Raw response: {raw}")

        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]

        parsed = json.loads(raw)
        print(f"[Gemini] Parsed: {parsed}")
        return parsed
    except Exception as e:
        print(f"[Gemini] Error: {repr(e)}")
        return []