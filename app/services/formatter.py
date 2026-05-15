def format_cart_response(results: list) -> str:
    # Filter out apps with no products found
    valid = [r for r in results if r["total"] > 0]

    if not valid:
        return "⚠️ Couldn't fetch prices right now. Please try again in a minute."

    cheapest = valid[0]
    lines = ["🛒 *Cheapest Cart*\n"]

    for i, r in enumerate(valid, 1):
        medal = ["🥇", "🥈", "🥉"][i-1] if i <= 3 else f"{i}."
        diff = ""
        if i > 1:
            extra = r["total"] - cheapest["total"]
            diff = f" (+₹{extra:.0f})"
        lines.append(f"{medal} *{r['app']}* — ₹{r['total']:.0f}{diff}")

        # Show itemized breakdown for cheapest
        if i == 1 and r["cart"]:
            for item_name, detail in r["cart"].items():
                lines.append(f"   • {detail['product']} — ₹{detail['price']:.0f}")

    if len(valid) > 1:
        savings = valid[-1]["total"] - cheapest["total"]
        if savings > 0:
            lines.append(f"\n💰 You save ₹{savings:.0f} vs {valid[-1]['app']}")

    return "\n".join(lines)
