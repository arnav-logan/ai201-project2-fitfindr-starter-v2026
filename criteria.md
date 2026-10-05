# Acceptance criteria — FitFindr

Five criteria that say what "working" means for this agent, written in unit 3
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"The agent handles errors"* is an opinion.
*"When search returns nothing, the agent stops before calling the second tool,
in 5 of 5 tries"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter one. A reason that says something about your tools, your loop, or the
data earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

**Two are written for you. You write three.**

---

## 1. A matching query completes all three tools

Given a query that matches at least one listing, the agent completes all three
tool calls and returns a fit card — in at least 4 of 5 tries.

**Why this target:**
4 of 5 because the happy path depends on inputs that can vary between runs. If the search uses a plain keyword match, some phrasings of a valid
query can miss. Also, the final fit card could be incorrect if it is missing the price.

---

## 2. An impossible query stops before the second tool

Given a query that matches no listings, the agent stops before calling
`suggest_outfit` and returns a message naming what to change — 5 of 5 tries.

**Why this target:**
5 of 5 is reasonable because this path is deterministic: an empty list from search_listings triggers the branch rule, and no model call is involved in deciding to stop or in producing the message.

---

## 3. Selected listing is the same accross a run of `suggest_outfit` and `create_fit_card`

Check the highest ranked listing in the list returned returned by `search_listings`. This listing should be the same as the `new_item` parameter in `suggest_outfit` and `create_fit_card` in 5 of 5 tries.

<!-- YOU WRITE THIS ONE.

     How would you know that the item your search found is the same item the
     next tool received? Name something countable or observable.

     This is the criterion people find hardest, because state failure doesn't
     look like state failure — it looks like a tool problem. Something that
     compares session["selected_item"] against what actually reached
     suggest_outfit is the shape you're after. -->



**Why this target:**
The state needs to be correct for sequential tool calls to function properly. It doesn't make sense to select a certain listing and then suggest an outfit and create a fit card using a different listing. So, it should aim for perfect accuracy.


---

## 4. Fit card descriptions must contain price and should be identifiable between similar listings

Each fit card needs to contain the price of the listing. The description of any given listing should be identifiable against the descriptions of similar listings 5 of 5 times.

<!-- YOU WRITE THIS ONE.

     The fit card calls a model, so the same input can produce different words
     each time. That's not a bug — it's the nature of the tool. So what would
     make it acceptable?

     Think about what you'd actually be unhappy to see. A caption that never
     mentions the price? Two different items producing the same opening
     sentence? A card longer than a caption anyone would post? Any of those can
     be turned into a number. -->



**Why this target:**
The fit card should contain the price, as it is a vital part of the listing. Fit card descriptions should be unique to the listing as they aim to describe the clothing item
in a presentable way, and each clothing item in different. So, it should aim for perfect accuracy.


---

## 5. If the wardrobe is empty, `suggest_outfit` always mentions that the wardrobe is empty in the output string

Intended behavior: `suggest_outfit` utilizes listings in the wardrobe. When the wardrobe is empty, the tool should notify the user and tell them that the wardrobe can be updated 4 of 5 times.

<!-- YOU WRITE THIS ONE TOO.

     Pick something you actually care about getting right. Speed, the empty
     wardrobe path, what happens when the model can't be reached, whether the
     search respects a price ceiling — anything, as long as it names a number
     or an observable outcome. -->



**Why this target:**
Since the wardrobe is an important part of this system, the output string should notify the user if the wardrobe is empty when using `suggest_outfit`. 4 of 5 times as there could be some inconsistency with model outputs.


---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 4 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 4. Something about the fit card

         The fit card is different every time.

         **Why this target:** ...

         > **Revised in unit 4:** For 5 different items, the 5 fit cards share
         > no opening sentence.
         >
         > **Why revised:** "different" wasn't checkable — two cards that
         > differed by one word still counted. The new version is something I
         > can actually score.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said the empty search stops it 5 of 5 times, but I got 3 of 5,
            so 3 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->
