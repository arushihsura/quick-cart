def format_cart_response(results: list[dict]) -> str:
    if not results:
        return "⚠️ Couldn't fetch prices right now. Please try again in a minute."

    cheapest = results[0]
    lines = ["🛒 *Cheapest Cart*\n"]

    for i, r in enumerate(results, 1):
        medal = ["🥇", "🥈", "🥉"][i - 1] if i <= 3 else f"{i}."
        diff = ""
        if i > 1:
            extra = r["total"] - cheapest["total"]
            diff = f" (+₹{extra:.0f})"
        lines.append(f"{medal} *{r['app']}* — ₹{r['total']:.0f}{diff}")

    savings = results[-1]["total"] - cheapest["total"] if len(results) > 1 else 0
    if savings > 0:
        lines.append(f"\n💰 You save ₹{savings:.0f} by ordering from {cheapest['app']}")

    return "\n".join(lines)
