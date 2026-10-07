"""
The FitFindr planning loop.

This is the file that makes FitFindr an agent rather than a script. It decides
which tool to run next based on what the last one returned.

If your loop calls all three tools no matter what comes back, you have a list
of function calls. A loop looks at the last result before it picks the next
step. **That branch is the graded part of this unit.**

Build and test your three tools in `tools.py` first. Then come here.

    python agent.py          runs both example paths below
"""

import config
import trace
from tools import search_listings, suggest_outfit, create_fit_card
from generate import ModelUnavailable
import re
import mcp_client

# ── session state ─────────────────────────────────────────────────────────────

def new_session(query: str, wardrobe: dict) -> dict:
    """
    A fresh session for one user interaction.

    The session is the single source of truth for a run. Every tool result goes
    in here, and the next tool reads it back out.

    You could pass values straight from one call to the next. It would work,
    and you would not be able to test it — you can't print a variable you have
    already overwritten. Going through the session is what makes the state
    visible, and unit 4 has you write a criterion about exactly that.

    Add fields if you need them.
    """
    return {
        "query": query,              # what the user typed
        "parsed": {},                # description / size / max_price you pulled out of it
        "search_results": [],        # everything search_listings returned
        "selected_item": None,       # the one you chose — goes into suggest_outfit
        "wardrobe": wardrobe,        # the user's wardrobe
        "outfit_suggestion": None,   # what suggest_outfit returned
        "fit_card": None,            # what create_fit_card returned
        "error": None,               # set when the run ended early
    }

_SIZE_RE = re.compile(
    r"\bsize\s*:?\s*((?:us\s*)?[a-z0-9]+(?:/[a-z0-9]+)?)",
    re.IGNORECASE,
)
_PRICE_RE = re.compile(
    r"(?:under|below|less than|up to|at most|max(?:imum)?|<=?)\s*\$?\s*(\d+(?:\.\d+)?)"
    r"|\$\s*(\d+(?:\.\d+)?)",
    re.IGNORECASE,
)


def _parse_query(query: str) -> dict:
    """
    Regex-based parse of the query into description, size, and max_price.
    Anything not recognized as a size or price stays in the description.
    """
    text = query or ""

    size = None
    size_match = _SIZE_RE.search(text)
    if size_match:
        size = size_match.group(1).strip()
        text = text[: size_match.start()] + " " + text[size_match.end():]

    max_price = None
    price_match = _PRICE_RE.search(text)
    if price_match:
        max_price = float(price_match.group(1) or price_match.group(2))
        text = text[: price_match.start()] + " " + text[price_match.end():]

    # Clean up leftover punctuation and extra whitespace
    description = re.sub(r"[,;:]+", " ", text)
    description = re.sub(r"\s+", " ", description).strip()

    return {"description": description, "size": size, "max_price": max_price}


def _no_results_message(parsed: dict) -> str:
    """Build a message that tells the user what they could change"""
    tips = []
    if parsed["size"]:
        tips.append(f"remove or change the size filter (size {parsed['size']})")
    if parsed["max_price"] is not None:
        tips.append(f"raise your price limit (currently ${parsed['max_price']:.0f})")
    tips.append("try simpler or different keywords, such as a single item type like 'tee' or 'jacket'")

    searched = parsed["description"] or "(nothing)"
    return f"No listings matched \"{searched}\". Try to " + ", or ".join(tips) + "."

# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    """
    ─────────────────────────────────────────────────────────────────────────
    IN UNIT 4 you come back and add two things:

      • Trace calls. One per step. `trace.step("search_listings", inputs=...,
        returned=...)` — see trace.py. Your README needs the output.

      • A handler for ModelUnavailable, so a bad key produces a message rather
        than a stack trace. The import is already at the top of this file.
    """

    session = new_session(query, wardrobe)
    step = "parse"
    count = 0

    while True:
        count += 1
        trace.check_iterations(count)  # raises if count passes MAX_ITERATIONS

        if step == "parse":
            session["parsed"] = _parse_query(session["query"])
            step = "search"

        elif step == "search":
            parsed = session["parsed"]
            results = mcp_client.call_tool(
                "search_listings",
                {"description" : parsed["description"], "size": parsed["size"], "max_price": parsed["max_price"]}
            )
            session["search_results"] = results

            # THE BRANCH: nothing came back, so stop before suggest_outfit
            if not results:
                session["error"] = _no_results_message(parsed)
                return session
            step = "select"

        elif step == "select":
            session["selected_item"] = session["search_results"][0]
            step = "outfit"

        elif step == "outfit":
            session["outfit_suggestion"] = suggest_outfit(
                session["selected_item"], session["wardrobe"]
            )
            step = "card"

        elif step == "card":
            session["fit_card"] = create_fit_card(
                session["outfit_suggestion"], session["selected_item"]
            )
            return session


# ── running it directly ───────────────────────────────────────────────────────

def _show(session: dict) -> None:
    if session["error"]:
        print(f"  stopped: {session['error']}")
        print(f"  fit_card is {session['fit_card']!r} — it should still be None here")
        return

    item = session["selected_item"] or {}
    print(f"  found:    {item.get('title')} — ${item.get('price')} on {item.get('platform')}")
    print(f"  outfit:   {session['outfit_suggestion']}")
    print(f"  fit card: {session['fit_card']}")


if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe

    print("=== A query the data can match ===")
    _show(run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    ))

    print("\n=== A query it can't ===")
    _show(run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    ))

    print(
        "\nThe second one should stop before the fit card. If both paths look "
        "the same,\nthe branch isn't doing anything yet."
    )
