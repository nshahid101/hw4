# Usability Improvements — HW 4 (Campus Customs)

Log of the 2 front-end usability improvements chosen from the list of 4 proposed for Problem 9.

## 1. Product filtering/search on the Products page

**What it is:** With 102 items and no way to narrow them down, browsing means scrolling through everything. Added a search box + filter by garment type (and maybe price range), so customers can actually find things.

**Why it helps:** A search box and category dropdown were added above the product grid. Customers can type a keyword (matched against the product name, description, and search tags) and/or pick a category (T-Shirts, Hoodies, Crewnecks, Sweatshirts, Quarter/Full-Zips, Jackets, Other) to instantly narrow the grid, with a running "X of 102 products" count and a clear empty-state message when nothing matches.

## 2. Interactive size picker on the product detail page

**What it is:** Right now sizes/stock are shown as a plain table. Swap it for clickable size buttons (grayed out and disabled when out of stock), which looks and feels much more like a normal shopping site.

**Why it helps:** The static sizes/stock table on the single-item page was replaced with clickable size buttons (XS–XXL). Out-of-stock sizes are visibly grayed out, struck through, and disabled from selection. Clicking an in-stock size shows a plain-English status line ("5 in stock in M." / "Only 2 left in L." / "XL is out of stock."), and the first in-stock size is auto-selected on page load so there's always a useful default.

## Verified in the running app
- Products page: filtering by "Hoodies" narrowed 102 → 27 products; adding a "bulldog" search on top of that narrowed it to exactly the 2 matching bulldog hoodies; an unmatched search term correctly showed the empty-state message.
- Product detail page: size buttons render for every product, out-of-stock sizes (e.g. XL on the Yale Bowl T Shirt) are visibly disabled and cannot be clicked, and selecting an in-stock size updates the status line with the real stock count from the database.

---

# Problem 10 — Style the Website

Six design suggestions chosen from a list of design ideas (font, color, hierarchy, product presentation, and chat feel) proposed for Problem 10.

## 1. Serif + sans-serif font pairing

**What it is:** Keep a serif (Georgia) for the logo and big headings for that collegiate feel, but switch prices, descriptions, nav links, and buttons to a clean sans-serif. Pairing a serif with a sans-serif is what the reference retail sites (Harvard Shop, Roll Tide) do — sans-serif throughout for legibility, serif reserved for branding.

**Why it helps:** Makes the product grid and prices easier to scan at commerce density, while the serif headings keep the collegiate brand feel. Implemented as a CSS variable swap (`--sans` now a system sans-serif stack), so every price, description, button, and nav link updated automatically with no per-component changes, while `h1`/`h2`/`h3` and the "Campus Customs" wordmark kept the serif.

## 2. Lean more on the Yale-blue brand color

**What it is:** Use the `--yale-blue` variable (already defined, previously only in the homepage hero) more consistently for brand "chrome" — nav bar, chat header, buttons — instead of a separate near-navy, similar to how the reference sites lead hard with one signature school color.

**Why it helps:** A single, consistent brand blue across the nav bar, the chat window header/send button, the selected size swatches, and the "From your chat" panel's Clear button makes the site read as more deliberately branded, rather than using two similar-but-different blues around the site. Plain navy is still used for body text/headings (as ink, not brand chrome).

## 3. "Shop by Category" row on the Home page

**What it is:** A row of category tiles (T-Shirts, Hoodies, Crewnecks, Sweatshirts, Quarter/Full-Zips, Jackets) between the hero and the product snapshot, giving browsers an immediate second path besides scrolling or chatting — mirrors the "collection block" pattern both reference sites use on their homepages.

**Why it helps:** Each tile shows a real, live count ("27 items") computed from the actual catalogue, and clicking one deep-links straight into the Products page with that category already filtered — so a customer can go from "I want a hoodie" to a filtered hoodie grid in one click from the homepage, instead of needing to visit Products first and filter manually.

## 4. Real, honest urgency badges on product cards

**What it is:** A small badge on the product card photo — "Only 9 left" or "Out of Stock" — computed directly from the real per-product stock total, not invented. Shown on every product card (Home, Products grid, chat results, and "You Might Also Like").

**Why it helps:** This is the single most purchase-motivating change on the list: genuine scarcity is one of the strongest, most honest nudges toward buying, and because it's computed from the same inventory numbers the rest of the site already uses, it can never show a false claim.

## 5. "You Might Also Like" on the product detail page

**What it is:** A row of real related products below the main product info — same garment type first, topped up with products sharing a search tag if needed — never a fabricated "bestseller" or invented recommendation.

**Why it helps:** Gives a customer who lands on one product page an easy next step toward buying something, instead of a dead end once they've read the description — the classic e-commerce "keep browsing" nudge, done here with genuinely similar real products.

## 6. Rename the chat to "Ask the Bulldog"

**What it is:** Renamed the floating chat button and panel header from a generic "Chat" / "Campus Customs Assistant" to "Ask the Bulldog" — giving the assistant a bit of the same school-spirit personality already written into its system prompt.

**Why it helps:** A named, branded assistant feels more like a helpful mascot-guide than a generic support widget, which should make customers more likely to actually open it and ask a question that leads to a sale.

## Verified in the running app
- Home page: nav bar, size-swatch buttons, and the chat header all render in Yale blue (`#00356b`); body text/prices render in the sans-serif font while headings stay serif (confirmed via computed styles, not just visually).
- "Shop by Category" tiles show real counts (e.g. Hoodies: 27 items) and clicking one navigates to `/products?category=Hoodies` with that filter already applied and the same 27-item count shown.
- A known low-stock product (Football Left Chest T Shirt, 9 total in stock) correctly shows an "ONLY 9 LEFT" badge on its card.
- A product detail page (Football Left Chest T Shirt) correctly shows a "You Might Also Like" row with 4 real same-category T-shirts.
- The chat button and panel header both read "Ask the Bulldog" instead of the old generic labels.
