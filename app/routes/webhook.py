from fastapi import APIRouter, Form, Request
from fastapi.responses import PlainTextResponse
from app.ai.parser import extract_grocery_list
from app.services.aggregator import compare_prices
from app.services.formatter import format_cart_response

router = APIRouter()

@router.post("/webhook")
async def whatsapp_webhook(
    request: Request,
    Body: str = Form(...),
    From: str = Form(...),
):
    print(f"\n{'='*50}")
    print(f"[Webhook] Message from: {From}")
    print(f"[Webhook] Body: {Body}")
    print(f"{'='*50}\n")

    # Step 1: Parse grocery list
    print("[Webhook] Calling Gemini parser...")
    items = await extract_grocery_list(Body)
    print(f"[Webhook] Parsed items: {items}")

    if not items:
        reply = "I couldn't find any grocery items. Try:\n\nNeed:\n2 milk\nbread\neggs"
        print("[Webhook] No items found, sending help message")
    else:
        print(f"[Webhook] Calling compare_prices for {len(items)} items...")
        results = await compare_prices(items, user_phone=From)
        print(f"[Webhook] Got results: {results}")
        reply = format_cart_response(results)

    print(f"[Webhook] Sending reply:\n{reply}\n")

    from twilio.twiml.messaging_response import MessagingResponse
    response = MessagingResponse()
    response.message(reply)
    return PlainTextResponse(str(response), media_type="application/xml")