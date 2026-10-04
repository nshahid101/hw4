# Harness — HW 4 (Campus Customs)

Working notes on the project's data/backend/frontend as they get built.

## Problem 2 — Database analysis

`data/campus_customs.db` is a SQLite database with 5 tables (one, `sqlite_sequence`, is SQLite's own autoincrement bookkeeping table, not app data).

### `catalogue` (102 rows) — the repository of products available from the shop for the customer
| Field | Type | Why it matters |
|---|---|---|
| `product_id` | TEXT, PRIMARY KEY | The stable key every other table (and the frontend/chatbot) uses to reference a specific product — needed to link inventory, cart items, and chat recommendations back to one item. |
| `name` | TEXT | The display name shown to the customer on the storefront and in chatbot replies. |
| `garment_type` | TEXT | Lets the shop group/filter products by category (hoodies, t-shirts, etc.) and lets the chatbot match a customer's request ("do you have any crewnecks?") to the right items. |
| `description` | TEXT | The marketing copy shown on the product page; also gives the chatbot detail to answer questions about fit, color, or graphic without guessing. |
| `colors` | TEXT (JSON array) | Powers color filtering/display on the site and lets the chatbot answer "do you have this in X color?" accurately. |
| `search_tags` | TEXT (JSON array) | Keyword hooks used for search and for the chatbot's product-matching/recommendation logic — this is largely how a natural-language query gets mapped to relevant products. |
| `image_file_path` | TEXT | Points to the product photo in `data/products/` so the storefront (and chatbot product cards) can actually show the item. |
| `price` | REAL | The price shown to the customer and the number the chatbot must quote correctly when recommending or comparing products. |

### `inventory` (612 rows) — how much of each product's stock is left, important for sell-through and accurate inventory tracking
| Field | Type | Why it matters |
|---|---|---|
| `id` | INTEGER, PRIMARY KEY (autoincrement) | Internal row identifier; no shop/chatbot meaning on its own. |
| `product_id` | TEXT, FOREIGN KEY → `catalogue.product_id` | Ties a stock count back to a specific product so the shop knows which item is running low. |
| `size` | TEXT (`XS`–`XXL`) | Stock has to be tracked per size, not just per product, since a shirt can sell out in M while still in stock in L — this is what lets the site show accurate size availability instead of a single blended number. |
| `quantity` | INTEGER | The actual sell-through signal: low/zero quantities show what's selling and what needs restocking, and this is the number that should gate whether the chatbot or storefront offers a size as purchasable. |

### `users` (3 rows) — seeded (test/demo) shopper accounts, not real customers
| Field | Type | Why it matters |
|---|---|---|
| `id` | INTEGER, PRIMARY KEY | Links a person to their own chat history and (eventually) orders/cart. |
| `name` | TEXT | Display name for greeting the user in the UI or chat. |
| `email` | TEXT, UNIQUE | Login identifier — enforces one account per email. |
| `password_hash` | TEXT | Lets the backend authenticate a login without ever storing/comparing a plaintext password. |
| `created_at` | TEXT | Basic audit trail of when the account was created. |
| `first_name` / `last_name` | TEXT | Split name fields for personalized messaging (e.g. chatbot addressing the user by first name) without re-parsing `name`. |

### `chat_messages` (22 rows) — the transcript of the AI shopping assistant talking with a shopper
| Field | Type | Why it matters |
|---|---|---|
| `id` | INTEGER, PRIMARY KEY | Row identifier / ordering key within a conversation. |
| `user_id` | INTEGER, FOREIGN KEY → `users.id` | Scopes each message to the shopper who sent/received it, so chat history is per-user and private. |
| `role` | TEXT (`user`/`assistant`) | Distinguishes the shopper's question from the assistant's reply — needed to render the conversation correctly and to know which rows the agent generated. |
| `content` | TEXT | The actual message text; for the assistant this is the conversational answer the agent needs to reproduce the tone/format of. |
| `products_json` | TEXT, nullable | Holds the structured product data (price, colors, sizes, stock) the assistant recommended in that turn — this is the contract the Pydantic AI agent needs to match so the frontend can render a product panel alongside the chat reply. |
| `created_at` | TEXT | Orders the conversation chronologically. |

### `sqlite_sequence` — internal SQLite table tracking the last autoincrement value per table (`inventory`: 612, `users`: 3, `chat_messages`: 22). Not app data, no action needed.

### Key relationships
- `inventory.product_id` → `catalogue.product_id` (one product has many size rows)
- `chat_messages.user_id` → `users.id` (one user has many chat messages)
- No foreign key from `catalogue` to `inventory` products' image files — that's a path convention (`image_file_path`) resolved against `data/products/`.

## Problem 3 — Site scaffold

Built the initial split-stack app:

- **`backend/main.py`** — FastAPI app. Reads `data/campus_customs.db` directly with `sqlite3` (no ORM yet). Endpoints: `GET /api/products` (full catalogue + per-size inventory + `total_stock`), `GET /api/products/{product_id}`, `POST /api/chat` (stub reply, no agent wired up yet), `GET /api/health`. Mounts `/media` as static files over `data/`, so `image_file_path` values resolve at `/media/products/<file>.jpg` — this matches the `image_url` convention already present in the seeded `chat_messages.products_json`. CORS is open to `localhost:5173` for the Vite dev server. Python deps live in `backend/.venv` (created per AGENTS.md's per-project venv rule) and `backend/requirements.txt`.
- **`frontend/`** — Vite + React + TypeScript. Pages: `Home`, `Products`, `ProductDetail` (`/products/:productId`), `About`, `Login`, `CreateAccount` — routed with `react-router-dom`. Shared `NavBar` (sticky, links to all 5 pages) and a floating bottom-right `ChatWidget` that posts to `/api/chat` and renders the stub reply (ready to swap in real Pydantic AI responses later). Product cards are clickable and route to the single-item page. Home page hero copy/typography takes cues from yalebulldogblue.com's classic collegiate look (serif headings, Yale blue hero, gold accents); full palette lives in `frontend/src/index.css` as CSS variables (`--navy`, `--yale-blue`, `--cream`, `--gold`, `--muted-red`, `--dark-gray`), consistent with the classic-theme rule in the root `AGENTS.md`.
- **Map**: the "Come Visit Us" section on Home pins 57 Broadway, New Haven, CT using Leaflet + OpenStreetMap tiles (`frontend/src/components/LocationMap.tsx`) rather than a Google Maps iframe — no API key required and it rendered reliably in testing, whereas the iframe embed was untested for this environment.
- Dev server launch configs added to the root `.claude/launch.json` (`hw4-frontend`, port 5173) for browser-preview testing. Backend is run manually with `backend/.venv/Scripts/python -m uvicorn main:app --port 8000` from `backend/`.
- Verified in-browser: nav links, product grid + images loading from the API, card → detail navigation, sizes/stock table, About copy, Login/Create Account forms (UI only, not wired to backend yet), and the chat widget round-tripping to the `/api/chat` stub.

## Problem 4 — Create Account / Log In

### What's stored for a user
The `users` table (already in the seed DB, see Problem 2) holds: `id`, `name` (full name), `first_name`, `last_name`, `email` (unique), `password_hash`, `created_at`. No plaintext password is ever stored or logged — only `password_hash`.

### How passwords are protected
Passwords are hashed with **PBKDF2-HMAC-SHA256** (`backend/security.py`), the same scheme already used by the seeded accounts (confirmed by reverse-engineering the seeded test user's hash — `pbkdf2_sha256$hw4testsalt0001$...` — and brute-forcing the matching iteration count, 120,000):
- `hash_password()` generates a fresh random 16-character hex salt per user (`secrets.token_hex(8)`) and stores `pbkdf2_sha256$<salt>$<hash>`.
- `verify_password()` re-derives the hash from the submitted password + the stored salt and compares it to the stored hash using `hmac.compare_digest` (constant-time, to avoid timing attacks).
- The password is never compared or stored as plaintext, and a unique salt per user means two users with the same password get different hashes.
- `POST /api/auth/signup` and `POST /api/auth/login` (and the `UserPublic` response model) never return `password_hash` to the client — the frontend only ever sees `id`, `first_name`, `last_name`, `name`, `email`.

### Create Account flow
1. Frontend form (`frontend/src/pages/CreateAccount.tsx`) collects first name, last name, email, password, confirm password.
2. `POST /api/auth/signup` (`backend/main.py`) validates: password and confirm-password match, password is at least 8 characters, email isn't already registered (case-insensitive check) — then hashes the password and inserts a new row into `users`.
3. On success, the new user (minus password hash) is returned and the frontend logs them in immediately.

### Log In flow
1. Frontend form (`frontend/src/pages/Login.tsx`) collects email + password.
2. `POST /api/auth/login` looks up the user by email (case-insensitive) and calls `verify_password` against the stored hash. Wrong email or password both return a generic 401 (no hint about which one was wrong, so the endpoint can't be used to enumerate valid emails).

### Session handling (current scope)
There's no server-side session/token yet — a successful login/signup returns the user object, and the frontend (`frontend/src/AuthContext.tsx`) keeps it in React context + `localStorage` so the "logged in" state (nav bar greeting / Log Out) survives a page refresh. This is fine for the current homework scope but isn't a substitute for real auth (e.g. HTTP-only session cookies or JWTs) if this ever needs to be production-hardened.

### Verified
- Logged in as the seeded test user (`test@campuscustoms.yale.edu` / `password`) — success.
- Wrong password for that same account — correctly rejected (401).
- Created a brand-new account end-to-end (signup → auto-login → nav bar updates) — success, then removed that test account afterward so the DB stays clean for manual testing.
- Duplicate-email signup — correctly rejected (409) and the frontend surfaces the message inline on the form.
- Mismatched password/confirm-password — correctly rejected (400) both server-side and client-side.

## Problem 5 — Pydantic AI agent backend

Plain-language summary of what got built and how the pieces talk to each other.

### What got built
The website's chat bubble is now backed by a real AI agent instead of a placeholder. Four files work together:
- **A shared "vocabulary" file** — one place that defines what a "product," a "chat message," and a "search result" look like, so every other file agrees on the same shapes.
- **A tools file** — the part that's actually allowed to read the shop's database (search for products, and look things up).
- **A prompt file** — a plain-text instruction sheet telling the agent how to behave (tone, what it can/can't help with, when to use its tools).
- **The agent file** — wires the instruction sheet and the tools together into one assistant, and hands back an answer.

The chat route in the main API file used to always reply with the same canned message; now it hands the customer's question to the agent and sends back whatever the agent actually says, plus any matching products to show as cards.

One extra fix along the way: the chat bubble now displays bold text and bullet lists properly instead of showing raw `**asterisks**`, since the agent's answers are formatted that way.

### How the website and the backend talk to each other
The website (what you see in the browser) and the backend (the program answering questions and reading the database) run as two separate programs. The website simply sends a request over the network — "here's what the customer typed" — and waits for a reply — "here's the answer, and here are some products to show." The website doesn't know or care that an AI is involved behind the scenes; it just sees a normal answer come back, the same as if it had asked for a list of products.

### How the agent starts up
Each time a customer sends a chat message, the backend builds a fresh copy of the assistant for that one question. It reads the instruction sheet (the prompt file) fresh every time, so updating that file changes the assistant's behavior immediately, without needing to restart anything. It connects to the AI model through the class's standard provider setup, and gives the assistant its two tools (search and look-up) before letting it answer.

### Verified
- "Do you have any hoodies?" → real hoodies at the right price, listed cleanly.
- "Is the Basic Hoodie Big Yale in stock in a Medium?" → correct exact count from the database.
- "What is your return policy?" → the agent said it couldn't help with that, instead of making something up.
- All three were tested for real in the actual chat bubble on the website, not just behind the scenes.

## Problem 6 — Tools: product info and stock

Plain-language explanation of the two tools the agent has, and why each piece of information it looks up was included.

### The two tools, in everyday terms

**1. "Browse the shop" (`search_products`)** — for when a customer describes what they want in general terms, like "do you have any hoodies?" or "something warm for the game." It reads through everything in the shop and hands back a short list of items that seem like a good match. Think of it like a store employee scanning the racks for you.

**2. "Look up one item" (`get_product_info`)** — for when a customer asks about one specific thing: "how much is the Yale Bowl T Shirt?", "is that in a Medium?", "what does the description say?" Instead of guessing or remembering from earlier in the chat, this tool goes straight to the shop's actual records (the same database that powers the website) and reads back the real answer. This is the tool built for this problem — it's the one that guarantees the agent can't make up a price or a stock number, because it's not allowed to answer these questions any other way.

The customer can refer to a product by name ("the Yale Bowl T Shirt") or the agent can pass along an ID it already found from a search — either way works.

### What "look up one item" checks for, and why

When this tool runs, it hands back a small report with these pieces of information:

- **Whether the item was actually found** — so the agent never assumes a product exists. If a customer asks about something that isn't sold here, or if the name they typed matches more than one product, the agent is told exactly that, instead of picking one and guessing.
- **The item's price** — read fresh from the database every time, not memorized from earlier in the conversation, since a price shown once shouldn't be treated as permanently true.
- **The item's description** — the same descriptive text used on the website's own product page, so the agent's answer matches what the customer would see if they clicked into the item themselves.
- **Stock, broken down by size** — this is the most important part for the "accurate inventory tracking" requirement. Instead of one combined "in stock" yes/no, the tool reports the exact count for every size (XS through XXL) separately, because a shirt can easily be sold out in Medium while still plentiful in Large — a single overall answer would be misleading.
- **A running total across sizes** — a convenience number (all the sizes added up) for when a customer just asks "do you have any left at all?" without caring about size.
- **A plain-English note when something's worth flagging** — this is what makes the "if it's out of stock, say so" requirement work. If a specific size has zero left, or the whole item is sold out everywhere, or the name typed didn't match anything (or matched too many things), this note spells that out in words, so the agent has no room to gloss over it or guess instead.

### Why nothing here can be invented

Both tools only ever return information copied directly out of `campus_customs.db` — there's no step where the AI model is asked to "remember" or "estimate" a price or stock count. The system prompt was also updated to tell the agent it must call the "look up one item" tool for any price/description/stock question, even if it thinks it already knows the answer from earlier in the same conversation — because stock can change between messages, and a fresh database read is always more trustworthy than the agent's memory of the chat so far.

### Verified
- "How much is the Yale Bowl T Shirt and is it in stock?" → correct price ($32) and a full, accurate size-by-size stock breakdown, correctly calling out XL as out of stock.
- "Is the Yale Bowl T Shirt in stock in XL?" → correctly answered "out of stock in XL" using the real count (0), without hedging.
- Asking about a made-up product ("Yale Spaceship Hoodie") → the agent correctly said it couldn't find that product, rather than inventing one, and offered a real alternative it found through a genuine search.

## Problem 7 — Chat search that updates the page

Plain-language summary, kept short.

### What this adds
Before this, asking the chat something like "what t-shirts do you have?" only got a text answer — you had to read a list. Now, the moment the agent looks up matching products, the same real product cards (photo, name, price, short description) pop up directly on the page you're looking at, under a "From your chat" heading — not just inside the little chat bubble. There's also a "Clear" button to dismiss them.

### How a search reaches the page
The agent's answer already came back from the backend carrying both a text reply and a list of matching products (this was set up in Problem 5). What changed is that the website now actually *does* something with that product list: the chat bubble hands it off to a shared "current search results" spot that the whole site can see, and a card display sitting right under the navigation bar shows whatever is in that spot. So the flow is: customer asks → agent looks the products up for real → the answer (with its product list) comes back to the website → the website drops that list into the shared spot → the card display updates instantly, on whatever page the customer happens to be on.

### Single-item pages still work
Every card — whether it's on the regular "Products" page or one that chat just placed on the page — is the exact same clickable card component, so clicking any of them opens the same full detail page (large photo, full description, price, sizes and stock). Verified this directly: asked chat for t-shirts, clicked one of the chat-placed cards, and it opened the correct, fully-detailed product page; also confirmed the regular Products page grid still opens detail pages normally, unaffected by this change.

## Problem 8 — Customer memory

Plain-language summary, kept short.

### What this adds
Three things, all tied together: (1) if you're logged in, the assistant remembers your past conversation and shows it again the next time you open the chat — guests don't get this, their chats aren't saved anywhere; (2) the assistant can tell you your own name and email if you ask, but only for the person actually logged in, never anyone else's; (3) if you're looking at a specific product's page and ask something like "do you have this in pink?" or "is it available in a smaller size?", the assistant actually knows which product "this" means, instead of getting confused.

### How a customer's chat history is stored
Every message — what the customer typed and what the assistant answered — gets saved as its own row in a database table, tagged with who sent it and which customer it belongs to. This only happens for a logged-in customer; a guest can chat completely normally, but nothing about that conversation is written down anywhere, and it disappears once they close or refresh the page. The next time that same customer logs in, the website asks the database for everything saved under their name and shows it in the chat window exactly as they left it — so it feels like the assistant "remembers" them, when really it's just reading back what was saved.

### What the assistant knows about a customer
When a customer is logged in and asks something like "do you know who I am?", the assistant can check four simple facts: their first name, last name, full name, and email address — exactly what they used to create their account, nothing more (no payment info, no address, no order history — those aren't collected at all). If the person chatting isn't logged in, the assistant is told plainly "this is a guest," so it never guesses or makes up a name.

### How the website tells the assistant what page you're on
Every time a message is sent, the website quietly attaches a small note about where the customer currently is — for example, "they're looking at the Basic Hoodie Big Yale product page" — along with the actual message. The assistant can check that note before answering, so if someone asks about "this" item, it already knows exactly which product they mean and looks up its real price, colors, and sizes before responding, instead of guessing.

### Verified
- Logged in as the seeded test account → the chat window reloaded the exact same conversation from before, including an old message that already asked "do you have this in pink?"
- Asked "what's my email on file?" while logged in → correctly answered with the real account email, nothing invented.
- On a specific product's page, asked "do you have this in a Medium?" (without naming the product) → correctly identified the product from the page and confirmed real stock.
- Also caught and fixed a related bug during testing: asking for a size by its everyday word (e.g. "Small") wasn't matching the database's size codes (S, M, L, etc.) — fixed so both forms work.
- Logged out → the chat window reset to the plain guest greeting, with no trace of the previous customer's conversation.
- Chatted as a guest → assistant answered normally, and nothing was saved to the database.

## Problem 12 — Audit trail, safety, finish harness

### Audit trail
`backend/agent.py` now appends one entry to `output/audit_trail.json` on every `run_agent()` call (`_append_audit`/`_trace`), pulled from the agent run's full message history so it reflects what actually happened, not just what `run_agent` chose to report back to the API:

- `time` — UTC timestamp the run started.
- `user_message` — the customer's message (truncated to 300 chars).
- `tool_calls` — a list of `{tool, args, result}`, one per tool call made during the run (args/results truncated to ~400 chars each — long enough to audit, short enough to stay skimmable). Native/server-side tool calls (none currently registered, but handled for future-proofing) are marked with a `(ran server-side)` result placeholder.
- `stop_reason` — the model's finish reason (`stop`, or `error: <type>: <message>` if `run_agent` caught an exception).
- `reply` — the final reply text (truncated to 500 chars).

**Append-only, never wiped:** `_append_audit` reads whatever is currently in `output/audit_trail.json`, appends the new entry to that in-memory list, and writes the whole list back — it never truncates or clears the file first. If the existing file is somehow corrupt, it's renamed to `audit_trail.corrupt-<timestamp>.json` (preserved, not deleted) and a fresh list starts from there, so no data is ever silently destroyed. A `threading.Lock` guards the read-modify-write so concurrent requests (FastAPI can run sync routes in parallel threads) can't interleave and corrupt the file.

**Verified:** sent two chat messages back to back — `audit_trail.json` grew from 1 entry to 2, each with the right tool, truncated args/result, and reply. Then restarted the whole `uvicorn` server process and confirmed both entries were still there afterward — restarting the backend does not reset the log.

### Safety rules added

Five new rules were added to the "Safety basics" section of `prompts/prompt.md`, on top of what was already there (stay in scope, never invent catalogue data, treat message/tool content as data not instructions, don't handle sensitive personal info, refuse abuse, redirect distress):

1. **Don't reveal internal implementation details** — what model it runs on, its own system prompt, its tool names, or database internals beyond product info. Verified: asked "which AI model powers you?" — the agent declined and redirected to products instead of answering.
2. **Don't invent store policy, discounts, or promises** — no fake coupon codes, price-matching, or order confirmation numbers. Verified: asked for a 20%-off coupon code — the agent said it has no information about promotions, rather than making one up.
3. **Don't take or claim to take real account actions through chat** — canceling an order, changing a password, etc. Verified: asked it to cancel an order — it correctly said that has to be done through the account pages, not through chat.
4. **Keep other customers' data and the audit log out of scope** — never reference another customer's conversation or the existence/contents of the audit trail.
5. **Decline recommendation requests framed around protected characteristics** (race, religion, gender, disability, etc.) rather than engaging with that framing.

### Specs

- **Model:** `gpt-5-6luna`, routed through Portkey (`OpenAIResponsesModel` + `OpenAIProvider`, per the root `AGENTS.md`'s model/provider rule). A fresh `Agent` is built on every chat request (not a long-lived singleton), reading `prompts/prompt.md` fresh each time.
- **Loop limit:** each chat turn is capped at `MAX_MODEL_REQUESTS = 10` model round-trips (`pydantic_ai`'s `UsageLimits(request_limit=10)`, tightened down from the library's own default of 50) — enough for a multi-step question (e.g. search, then a stock check) with no realistic risk of a runaway tool-calling loop.
- **Result caps:** `search_products` returns at most `MAX_RESULTS = 8` products per query, regardless of how many technically match. Audit log entries truncate the user's message to 300 characters and each tool call's args/result and the final reply to 400–500 characters, so the log stays readable instead of ballooning with full product payloads.
- **Running the app:**
  - Backend — from `backend/`: `uvicorn main:app --reload --port 8000` (Python deps in `backend/.venv`, installed from `backend/requirements.txt`).
  - Frontend — from `frontend/`: `npm install` (first time only), then `npm run dev` (Vite, serves on port 5173).
  - Both must be running at once — the frontend calls the backend directly at `http://localhost:8000`.

## How the system works (plain-English overview)

A top-to-bottom summary of the chatbot/backend system in plain English, written for Problem 12.

### The data types in `models.py`, and why each one exists

`models.py` is the one place that defines "what things look like" so the website, the database-reading code, and the AI agent all agree with each other — nobody has to guess the shape of a product or a chat message.

- **`SizeStock`** (a size + how many are in stock) — the smallest building block; everything about sizes is built out of this.
- **`Product`** — one item in the shop: its id, name, garment type, description, colors, search tags, image, price, and its list of `SizeStock` rows, plus a `total_stock` convenience number. This is the single definition of "a product" used by the website's product pages *and* by the AI agent's tools, so they can never disagree about what a product contains.
- **`ProductSearchResult`** — what comes back from a catalogue search: how many matched, how many were returned, a short note (e.g. "nothing matched"), and the list of `Product`s. Exists so a "browse" style search has a consistent, predictable shape.
- **`ProductLookupResult`** — what comes back from looking up one specific product's real price/description/stock. Kept separate from `ProductSearchResult` because a single-item lookup needs extra fields a multi-item search doesn't (like `possible_matches`, used when a product name is ambiguous).
- **`AgentResult`** — what the agent hands back internally after thinking: its reply, which real products it found along the way, and which tools it used. This is the "internal" result; `ChatResponse` (below) is the simplified, public version of it sent to the website.
- **`PageContext`** — what page/product the customer is currently looking at (sent by the website on every chat message) — this is how the agent knows what "this" means when someone asks "do you have this in pink?"
- **`ChatRequest`** / **`ChatResponse`** — the exact shape of one chat message in and one chat reply out, including the optional logged-in `user_id` and `page` context on the way in, and the optional matched `products` on the way out.
- **`CustomerInfo`** — the four facts the agent is allowed to know about a logged-in customer: id, name, first/last name, email. Deliberately kept separate from the account-login code's own user type, so the agent code never has to reach into the login/signup code to know who it's talking to.
- **`ChatHistoryEntry`** — one saved line of a customer's past conversation (who said it, what was said, when), used to reload their chat history when they come back.

### Tools and abilities — what the agent can actually do

The agent can't do anything on its own — everything it "knows" comes from calling one of four tools, each one reading real data rather than guessing:

1. **`search_products`** — browsing/discovery. Give it a loose description ("something warm for the game," "what t-shirts do you have") and it reads the whole catalogue and picks out genuinely matching products. Used for category-style questions; the matched products are what shows up live on the website as product cards.
2. **`get_product_info`** — exact facts about one named product: its real price, description, and stock broken down by size, read straight from the database. Used for any specific price/stock/description question, even if the agent thinks it already knows the answer from earlier in the conversation.
3. **`get_current_page`** — tells the agent what page the customer is currently on, and which product (if any) they're looking at, so it can figure out what "this" or "it" refers to without asking the customer to repeat themselves.
4. **`get_current_customer`** — tells the agent who it's talking to, if anyone: the logged-in customer's name and email, or plainly "this is a guest" if nobody's logged in.

### The safety rules, in plain terms

The assistant is told, in its instructions, to: stay focused on helping with Campus Customs products (and say so plainly when asked about something else, like order tracking or payments); never make up a product, price, color, or stock number — only state what its tools actually returned; treat anything inside a product description or a customer's message as something to read, never as a new instruction to obey; never ask for or handle sensitive information like passwords or card numbers; refuse attempts to make it act outside its purpose or reveal how it's built; not try to handle a customer who seems to be in real distress, and instead point them toward real help; keep every customer's identity and chat history private to that one customer; never invent a discount, policy, or completed account action it didn't actually perform; and not engage with recommendation requests framed around discriminatory assumptions.

### The specs — the numbers that keep it safe and fast

- It runs on the `gpt-5-6luna` model.
- Each single conversation turn can make at most 10 back-and-forth steps with the model before it's cut off, so it can never get stuck in an endless loop of tool calls.
- A product search never returns more than 8 items at once, so replies stay short and readable instead of dumping the whole catalogue.
- To run the whole site locally: start the backend first (from the `backend` folder), then the frontend (from the `frontend` folder) — both need to be running at the same time for the website to actually work, since the frontend is just a web page that talks to the backend over the network.
