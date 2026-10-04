"""Agent tools + shared product data access.

get_products()/get_product() read the catalogue+inventory tables and are used
by both the FastAPI product endpoints (main.py) and the agent tools below, so
there is one source of truth for what a "product" looks like.

search_products ranks the catalogue semantically via one extra model call —
the catalogue is small enough (102 rows) to hand to the model directly rather
than building a vector store, so paraphrases ("something warm for winter")
match even without shared keywords. Use it for browsing/discovery.

get_product_info is a plain DB lookup (no LLM call, so nothing it returns can
be invented) for the grounded facts about one specific product — description,
price, and exactly how many are in stock per size. Use it whenever the
customer asks about price, description, or stock for a product they've
already named.

save_chat_message/get_chat_history read and write user_chat_history — the
per-customer chat log main.py uses to persist and reload a logged-in
customer's conversation (never for guests).
"""

from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from models import (
    ChatHistoryEntry,
    Product,
    ProductLookupResult,
    ProductSearchResult,
    SizeStock,
)

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DB_PATH = ROOT / "data" / "campus_customs.db"
load_dotenv(ROOT / ".env")
load_dotenv(ROOT.parent / ".env")

SIZE_ALIASES = {
    "XS": "XS", "EXTRA SMALL": "XS", "X-SMALL": "XS",
    "S": "S", "SMALL": "S",
    "M": "M", "MEDIUM": "M", "MED": "M",
    "L": "L", "LARGE": "L",
    "XL": "XL", "EXTRA LARGE": "XL", "X-LARGE": "XL",
    "XXL": "XXL", "2XL": "XXL", "XX-LARGE": "XXL", "EXTRA EXTRA LARGE": "XXL",
}


def _normalize_size(size: str) -> str:
    """Map a customer's size word ("Small", "medium", "2XL", ...) to the
    catalogue's size code (S, M, XXL, ...) so a plain-English size question
    still matches real inventory rows. Falls back to the input, uppercased,
    if it's not a recognized alias — the caller still handles a no-match.
    """
    return SIZE_ALIASES.get(size.strip().upper(), size.strip().upper())


MODEL_NAME = "gpt-5-6luna"
PORTKEY_BASE_URL = os.getenv("PORTKEY_BASE_URL", "https://api.portkey.ai/v1").rstrip("/")
MAX_RESULTS = 8

_RANK_SCHEMA = {
    "type": "json_schema",
    "name": "product_ranking",
    "schema": {
        "type": "object",
        "properties": {
            "product_ids": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Catalogue product_ids, most relevant to the query first.",
            }
        },
        "required": ["product_ids"],
        "additionalProperties": False,
    },
    "strict": True,
}


def _client() -> OpenAI:
    api_key = os.getenv("PORTKEY_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("PORTKEY_API_KEY is not set (put it in a .env file).")
    return OpenAI(
        api_key=api_key,
        base_url=PORTKEY_BASE_URL,
        default_headers={"x-portkey-api-key": api_key},
    )


def _connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _row_to_product(row: sqlite3.Row, inventory_rows: list[sqlite3.Row]) -> Product:
    inventory = [SizeStock(size=r["size"], quantity=r["quantity"]) for r in inventory_rows]
    return Product(
        product_id=row["product_id"],
        name=row["name"],
        garment_type=row["garment_type"],
        description=row["description"],
        colors=json.loads(row["colors"]),
        search_tags=json.loads(row["search_tags"]),
        image_url=f"/media/{row['image_file_path']}",
        price=row["price"],
        inventory=inventory,
        total_stock=sum(i.quantity for i in inventory),
    )


def get_products() -> list[Product]:
    """All catalogue products with their inventory. Used by GET /api/products."""
    conn = _connection()
    try:
        rows = conn.execute("SELECT * FROM catalogue ORDER BY name").fetchall()
        inventory = conn.execute("SELECT * FROM inventory").fetchall()
    finally:
        conn.close()

    inventory_by_product: dict[str, list[sqlite3.Row]] = {}
    for row in inventory:
        inventory_by_product.setdefault(row["product_id"], []).append(row)

    return [_row_to_product(row, inventory_by_product.get(row["product_id"], [])) for row in rows]


def get_product(product_id: str) -> Product | None:
    """One catalogue product with its inventory, or None if it doesn't exist."""
    conn = _connection()
    try:
        row = conn.execute("SELECT * FROM catalogue WHERE product_id = ?", (product_id,)).fetchone()
        if row is None:
            return None
        inventory_rows = conn.execute(
            "SELECT * FROM inventory WHERE product_id = ?", (product_id,)
        ).fetchall()
    finally:
        conn.close()

    return _row_to_product(row, inventory_rows)


def _catalog_line(product: Product) -> str:
    """One line per product for the ranking prompt: id | name | garment_type | colors | price."""
    colors = ", ".join(product.colors)
    return f"{product.product_id} | {product.name} | {product.garment_type} | {colors} | ${product.price:.2f}"


def search_products(query: str, limit: int = MAX_RESULTS) -> ProductSearchResult:
    """Semantically search the Campus Customs catalogue.

    This ranks products by meaning, not keyword overlap — an LLM reads the
    whole catalogue and picks what genuinely matches, so requests like
    "something warm for a game" or "a gift for my Yale grad" work even if
    they don't share exact words with the product text.

    Args:
        query: A natural-language description of what the customer wants —
            a garment type, sport, residential college, color, occasion, or
            any mix of these.
        limit: Maximum products to return (capped at 8).
    """
    limit = max(1, min(limit, MAX_RESULTS))
    products = get_products()
    catalog = "\n".join(_catalog_line(p) for p in products)
    prompt = (
        "Catalogue (one product per line, `product_id | name | garment_type | colors | price`):\n"
        f"{catalog}\n\n"
        f"Query: {query!r}\n\n"
        f"Return the product_ids of the products that genuinely match this query, ranked "
        f"most relevant first, at most {limit} of them. Return fewer than {limit} if fewer "
        "genuinely match — never pad the list with irrelevant products."
    )

    try:
        response = _client().responses.create(
            model=MODEL_NAME,
            input=[
                {
                    "role": "system",
                    "content": "You rank Campus Customs products by semantic relevance to a search query.",
                },
                {"role": "user", "content": prompt},
            ],
            text={"format": _RANK_SCHEMA},
        )
        ids = json.loads(response.output_text)["product_ids"]
    except Exception as exc:
        return ProductSearchResult(
            total_matches=0,
            returned=0,
            note=f"Semantic search failed: {type(exc).__name__}: {exc}",
        )

    by_id = {p.product_id: p for p in products}
    matched = [by_id[i] for i in ids if i in by_id][:limit]
    return ProductSearchResult(
        total_matches=len(matched),
        returned=len(matched),
        note="" if matched else "No products matched that query.",
        products=matched,
    )


def _find_product(identifier: str) -> tuple[Product | None, list[str]]:
    """Resolve a product_id or product name to one Product.

    Tries, in order: exact product_id, exact case-insensitive name match,
    then a case-insensitive substring match on name. Returns (product, [])
    on a clean match, or (None, candidate_names) if the identifier matched
    zero or more-than-one product by name (so the caller can ask the
    customer to be more specific instead of guessing).
    """
    exact = get_product(identifier)
    if exact is not None:
        return exact, []

    products = get_products()
    needle = identifier.strip().lower()

    exact_name_matches = [p for p in products if p.name.lower() == needle]
    if len(exact_name_matches) == 1:
        return exact_name_matches[0], []

    substring_matches = [p for p in products if needle in p.name.lower()]
    if len(substring_matches) == 1:
        return substring_matches[0], []

    candidates = exact_name_matches or substring_matches
    return None, [p.name for p in candidates]


def get_product_info(identifier: str, size: str | None = None) -> ProductLookupResult:
    """Look up the real, current description, price, and stock for one product.

    This is a direct database read — every field it returns (description,
    price, stock per size) comes straight from campus_customs.db, never
    guessed or remembered from earlier in the conversation. Use this any
    time a customer asks what something costs, what it's like, or whether
    it's in stock (overall or in a specific size).

    Args:
        identifier: The product's product_id (if already known from a prior
            search_products result) or its name, e.g. "Yale Bowl T Shirt".
        size: A size, either the catalogue code (XS, S, M, L, XL, XXL) or a
            plain word ("Small", "Medium", "2XL", ...) — both are accepted.
            Omit to see stock for every size.
    """
    product, candidate_names = _find_product(identifier)

    if product is None:
        if candidate_names:
            return ProductLookupResult(
                found=False,
                note=(
                    f"'{identifier}' matches more than one product: "
                    f"{', '.join(candidate_names)}. Ask the customer which one they mean."
                ),
                possible_matches=candidate_names,
            )
        return ProductLookupResult(
            found=False, note=f"No product in the catalogue matches '{identifier}'."
        )

    sizes = product.inventory
    note = ""
    if size:
        normalized = _normalize_size(size)
        matched_size = [s for s in product.inventory if s.size.upper() == normalized]
        if not matched_size:
            note = f"'{size}' isn't a size Campus Customs carries for this product."
            sizes = []
        else:
            sizes = matched_size
            if sizes[0].quantity == 0:
                note = f"Out of stock in size {sizes[0].size} right now."
    elif product.total_stock == 0:
        note = "Out of stock in every size right now."

    return ProductLookupResult(
        found=True,
        product_id=product.product_id,
        name=product.name,
        description=product.description,
        price=product.price,
        sizes=sizes,
        total_stock=sum(s.quantity for s in sizes),
        note=note,
    )


def save_chat_message(
    user_id: int, role: str, content: str, products: list[Product] | None = None
) -> None:
    """Append one turn to user_chat_history — only ever called for a logged-in
    customer (see main.py's /api/chat route). Guest chats are never written
    here, per the "chat history only for logged-in users" requirement.
    """
    products_json = json.dumps([p.model_dump() for p in products]) if products else None
    conn = _connection()
    try:
        conn.execute(
            "INSERT INTO user_chat_history (user_id, role, content, products_json) "
            "VALUES (?, ?, ?, ?)",
            (user_id, role, content, products_json),
        )
        conn.commit()
    finally:
        conn.close()


def get_chat_history(user_id: int) -> list[ChatHistoryEntry]:
    """All saved messages for one logged-in customer, oldest first — used to
    reload their conversation when they return to the site.
    """
    conn = _connection()
    try:
        rows = conn.execute(
            "SELECT role, content, created_at FROM user_chat_history "
            "WHERE user_id = ? ORDER BY id",
            (user_id,),
        ).fetchall()
    finally:
        conn.close()

    return [
        ChatHistoryEntry(role=r["role"], content=r["content"], created_at=r["created_at"])
        for r in rows
    ]
