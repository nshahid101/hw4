"""Pydantic models shared by main.py, tools.py, and agent.py.

Keeping Product/SizeStock here (rather than duplicated in main.py) means the
FastAPI product endpoints and the agent's tools always agree on what a
"product" looks like.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class SizeStock(BaseModel):
    size: str
    quantity: int


class Product(BaseModel):
    product_id: str
    name: str
    garment_type: str
    description: str
    colors: list[str]
    search_tags: list[str]
    image_url: str
    price: float
    inventory: list[SizeStock]
    total_stock: int


class ProductSearchResult(BaseModel):
    """What the search_products tool returns to the agent."""

    total_matches: int
    returned: int
    note: str = ""
    products: list[Product] = Field(default_factory=list)


class ProductLookupResult(BaseModel):
    """What the get_product_info tool returns to the agent — the grounded,
    database-backed answer to "what does this cost / what is it / is it in
    stock" for one specific product. Every field here is read straight from
    campus_customs.db so the agent never has to (and never should) guess.
    """

    found: bool
    product_id: str = ""
    name: str = ""
    description: str = ""
    price: float | None = None
    sizes: list[SizeStock] = Field(default_factory=list)
    total_stock: int = 0
    note: str = ""
    possible_matches: list[str] = Field(default_factory=list)


class AgentResult(BaseModel):
    """What run_agent() returns to main.py's /api/chat route."""

    reply: str
    products: list[Product] = Field(default_factory=list)
    tools_used: list[str] = Field(default_factory=list)


class PageContext(BaseModel):
    """What page/product the customer is looking at when they send a chat
    message — sent by the frontend on every request (logged in or not) so
    the agent can resolve "this"/"it" questions like "do you have this in
    pink?" on a product detail page. See the get_current_page agent tool.
    """

    page: str  # "home" | "products" | "product_detail" | "about" | "login" | "create_account"
    product_id: str | None = None


class ChatRequest(BaseModel):
    """Body of POST /api/chat — one message from the website's chat widget."""

    message: str = Field(min_length=1)
    user_id: int | None = None
    page: PageContext | None = None


class ChatResponse(BaseModel):
    """Response of POST /api/chat.

    `products`, when present, are the products the agent's search_products
    tool matched this turn — the frontend renders these as product cards
    next to the chat reply (see frontend/src/components/ChatWidget.tsx and
    ProductCard.tsx), the same way the seeded chat_messages.products_json
    data paired a reply with a product panel.
    """

    reply: str
    products: list[Product] | None = None


class CustomerInfo(BaseModel):
    """The logged-in customer's identity, as seen by the get_current_customer
    agent tool. Kept separate from main.py's UserPublic (the signup/login API
    response) so agent.py never has to import from main.py.
    """

    id: int
    name: str
    first_name: str | None = None
    last_name: str | None = None
    email: str


class ChatHistoryEntry(BaseModel):
    """One saved row from the user_chat_history table, as returned by
    GET /api/chat/history for reloading a returning customer's conversation.
    """

    role: str
    content: str
    created_at: str
