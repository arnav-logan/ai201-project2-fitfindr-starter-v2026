"""
The three FitFindr tools.

Each one is a standalone function you can call and test on its own, before any
of them are wired into the loop. Build and test them one at a time — three
untested tools joined by a loop is one problem that looks like six, because you
can't tell which layer is lying to you.

    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)             → str
    create_fit_card(outfit, new_item)              → str

All three are stubs right now. They run and they do nothing — that's the
starting position and it's deliberate.

⚠️ Before you write any of them, fill in the **Tool Inventory** section of your
README (Milestone 2). Four lines per tool: what it does, each input with its
type, exactly what it returns, and what it returns when it has nothing to give.
That last line is what your loop branches on. "Returns a list" earns nothing —
the description has to say what is *in* the list.
"""

import config  # noqa: F401 — you'll use this in search_listings
from generate import generate
from utils.data_loader import load_listings
import re

# Words to cut out from user input
_STOPWORDS = {
    "a", "an", "the", "and", "or", "for", "in", "on", "with", "of", "to",
    "i", "me", "my", "want", "need", "looking", "find", "show", "some",
}


def _tokenize(text: str) -> set[str]:
    # Function to split text description (uses Regex)
    tokens = set()
    for word in re.findall(r"[a-z0-9]+", text.lower()):
        if len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
            word = word[:-1]  # "tees" -> "tee", "jeans" -> "jean"
        tokens.add(word)
    return tokens

def _size_matches(requested: str, listing_size: str | None) -> bool:
    # Token-based size match that is case insensitive
    if not listing_size:
        return False
    wanted = set(re.findall(r"[a-z0-9]+", requested.lower()))
    have = set(re.findall(r"[a-z0-9]+", listing_size.lower()))
    return bool(wanted) and wanted <= have


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the listings data for items matching a description, and optionally a
    size and a price ceiling.

    Returns a list of matching listing dicts, best match first. Returns an
    empty list when nothing matches.
    """
    keywords = _tokenize(description or "") - _STOPWORDS
    if not keywords:
        return []

    scored = []
    for listing in load_listings():
        # 1. Hard filters
        if max_price is not None and listing["price"] > max_price:
            continue
        if size is not None and not _size_matches(size, listing.get("size")):
            continue

        # 2. Score by keyword overlap. Title and tag matches count extra
        #    because they are the most deliberate descriptions of an item.
        title_tokens = _tokenize(listing.get("title") or "")
        tag_tokens = _tokenize(" ".join(listing.get("style_tags") or []))
        other_tokens = _tokenize(
            " ".join(
                [
                    listing.get("description") or "",
                    listing.get("category") or "",
                    " ".join(listing.get("colors") or []),
                    listing.get("brand") or "",  # brand is often None
                ]
            )
        )

        score = 0
        for kw in keywords:
            if kw in title_tokens:
                score += 3
            if kw in tag_tokens:
                score += 2
            if kw in other_tokens:
                score += 1

        # 3. Drop zero scores
        if score > 0:
            scored.append((score, listing))

    # 4. Best score first; cheaper listing wins ties
    scored.sort(key=lambda pair: (-pair[0], pair[1]["price"]))
    return [listing for _, listing in scored[: config.SEARCH_RESULT_LIMIT]]


def _describe_wardrobe_item(item) -> str:
    # Return a wardrobe item's name exactly as written
    if isinstance(item, str):
        return item.strip()
    if isinstance(item, dict):
        # Try the most likely name fields; fall back to the whole dict.
        for key in ("name", "title", "description"):
            if item.get(key):
                return str(item[key]).strip()
    return str(item)


def _describe_listing(item: dict) -> str:
    # Return a one-line summary of the listing for the prompt
    colors = ", ".join(item.get("colors") or []) or "unspecified colors"
    tags = ", ".join(item.get("style_tags") or []) or "no style tags"
    brand = item.get("brand") or "no brand"  # brand is often None
    return (
        f"{item.get('title', 'Untitled item')} "
        f"(category: {item.get('category', 'unknown')}, colors: {colors}, "
        f"style: {tags}, brand: {brand}, size: {item.get('size', 'unknown')}, "
        f"condition: {item.get('condition', 'unknown')})"
    )

# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    items = (wardrobe or {}).get("items") or []
    listing_text = _describe_listing(new_item)

    if not items:
        prompt = (
            "You are a friendly thrift-fashion stylist.\n\n"
            f"The user is considering this second-hand find:\n{listing_text}\n\n"
            "Suggest TWO different outfits built around this item. The user "
            "has no saved wardrobe, so use general, commonly owned pieces "
            "(e.g. 'straight-leg jeans', 'white sneakers'). Give each outfit "
            "a short label and one or two sentences. Do not mention that "
            "there is no wardrobe; that note is added separately."
        )
        note = (
            "These are general outfit ideas because no wardrobe is saved yet.\n\n"
        )
    else:
        wardrobe_text = "\n".join(f"- {_describe_wardrobe_item(i)}" for i in items)
        prompt = (
            "You are a friendly thrift-fashion stylist.\n\n"
            f"The user is considering this second-hand find:\n{listing_text}\n\n"
            f"Here is what they already own:\n{wardrobe_text}\n\n"
            "Suggest TWO different outfits built around the new item. Each "
            "outfit must include at least one piece from the user's wardrobe, "
            "and you must name those pieces exactly as written in the list "
            "above. Do not invent wardrobe pieces the user doesn't own. Give "
            "each outfit a short label and one or two sentences."
        )
        note = ""

    try:
        response = generate(prompt)
    except Exception:
        response = ""

    response = (response or "").strip()
    if not response:
        #  Never return an empty string
        title = new_item.get("title", "this item")
        response = (
            f"I couldn't generate outfit ideas for {title} right now. "
        )

    return note + response


def _format_price(price) -> str:
    # Fucntion to write the price with digits, ex: 25.0 -> '$25', 24.5 -> '$24.50'
    try:
        value = float(price)
    except (TypeError, ValueError):
        return ""
    return f"${value:.0f}" if value == int(value) else f"${value:.2f}"

# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
     # 1. Guard: no outfit -> helpful message, no model call
    if not outfit or not outfit.strip():
        return (
            "I can't write a fit card yet because there's no outfit to build "
            "it around. Run the outfit suggestion step first, then try again."
        )

    title = new_item.get("title", "this find")
    platform = new_item.get("platform") or "a resale app"
    price_text = _format_price(new_item.get("price"))
    colors = ", ".join(new_item.get("colors") or []) or "unspecified colors"
    tags = ", ".join(new_item.get("style_tags") or []) or "no style tags"
    brand = new_item.get("brand") or "no brand"  # brand is often None

    # 2. Build the prompt
    prompt = (
        "You write captions for social media posts about second-hand fashion "
        "finds. Write like a real person posting their thrift haul, not like "
        "a product description.\n\n"
        f"The find: {title}\n"
        f"Price: {price_text or 'unknown'}\n"
        f"Platform: {platform}\n"
        f"Colors: {colors}\n"
        f"Style: {tags}\n"
        f"Brand: {brand}\n\n"
        f"How it could be worn:\n{outfit.strip()}\n\n"
        "Rules:\n"
        "- Write exactly 2 to 4 sentences.\n"
        f"- Mention the price written with digits ({price_text}) once.\n"
        f"- Mention the platform ({platform}) once.\n"
        "- Mention the item once and be specific about the vibe.\n"
        "- No hashtags, no bullet points, no quotation marks around the caption.\n"
        "- Output only the caption."
    )

    # 3. Call the model once
    try:
        caption = (generate(prompt) or "").strip().strip('"')
    except Exception:
        caption = ""

    if caption:
        return caption

    # 4. Fallback so the tool never returns ""
    price_part = f" for {price_text}" if price_text else ""
    return (
        f"Thrift find of the week: {title}{price_part} on {platform}. "
    )