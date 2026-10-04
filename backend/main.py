"""Campus Customs API — serves product data + images to the frontend,
handles account creation/login, and runs the Pydantic AI agent behind
POST /api/chat (see agent.py, tools.py, models.py, prompts/prompt.md).

Run from backend/:  uvicorn main:app --reload --port 8000
"""

import sqlite3
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr, field_validator

from agent import run_agent
from models import AgentResult, ChatHistoryEntry, ChatRequest, ChatResponse, CustomerInfo, Product
from security import hash_password, verify_password
from tools import get_chat_history, get_product, get_products, save_chat_message

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DB_PATH = DATA_DIR / "campus_customs.db"

app = FastAPI(title="Campus Customs API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serves data/products/*.jpg at /media/products/*.jpg, matching the
# image_url convention already used in the seeded user_chat_history data.
app.mount("/media", StaticFiles(directory=DATA_DIR), name="media")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.get("/api/products", response_model=list[Product])
def list_products():
    return get_products()


@app.get("/api/products/{product_id}", response_model=Product)
def get_one_product(product_id: str):
    product = get_product(product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


class UserPublic(BaseModel):
    id: int
    first_name: Optional[str]
    last_name: Optional[str]
    name: str
    email: str


class SignupRequest(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str
    confirm_password: str

    @field_validator("first_name", "last_name")
    @classmethod
    def not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("This field can't be blank")
        return value.strip()

    @field_validator("password")
    @classmethod
    def min_length(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters")
        return value


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@app.post("/api/auth/signup", response_model=UserPublic, status_code=201)
def signup(request: SignupRequest):
    if request.password != request.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    email = request.email.lower()
    conn = get_connection()
    try:
        existing = conn.execute("SELECT id FROM users WHERE lower(email) = ?", (email,)).fetchone()
        if existing is not None:
            raise HTTPException(status_code=409, detail="An account with this email already exists")

        full_name = f"{request.first_name} {request.last_name}"
        password_hash = hash_password(request.password)
        cursor = conn.execute(
            """
            INSERT INTO users (name, email, password_hash, first_name, last_name)
            VALUES (?, ?, ?, ?, ?)
            """,
            (full_name, email, password_hash, request.first_name, request.last_name),
        )
        conn.commit()
        new_user = conn.execute("SELECT * FROM users WHERE id = ?", (cursor.lastrowid,)).fetchone()
    finally:
        conn.close()

    return UserPublic(
        id=new_user["id"],
        first_name=new_user["first_name"],
        last_name=new_user["last_name"],
        name=new_user["name"],
        email=new_user["email"],
    )


@app.post("/api/auth/login", response_model=UserPublic)
def login(request: LoginRequest):
    conn = get_connection()
    try:
        user = conn.execute(
            "SELECT * FROM users WHERE lower(email) = ?", (request.email.lower(),)
        ).fetchone()
    finally:
        conn.close()

    if user is None or not verify_password(request.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    return UserPublic(
        id=user["id"],
        first_name=user["first_name"],
        last_name=user["last_name"],
        name=user["name"],
        email=user["email"],
    )


def _get_customer(user_id: int) -> CustomerInfo | None:
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    finally:
        conn.close()
    if row is None:
        return None
    return CustomerInfo(
        id=row["id"],
        name=row["name"],
        first_name=row["first_name"],
        last_name=row["last_name"],
        email=row["email"],
    )


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    # Page context is used for every chat (guest or logged in) so the agent
    # can resolve "this"/"it" on a product page. Only a logged-in customer's
    # messages get saved to user_chat_history — guests can still chat, they
    # just don't get a saved/reloadable history.
    customer = _get_customer(request.user_id) if request.user_id is not None else None

    if customer is not None:
        save_chat_message(customer.id, "user", request.message)

    result = AgentResult.model_validate(run_agent(request.message, user=customer, page=request.page))

    if customer is not None:
        save_chat_message(customer.id, "assistant", result.reply, result.products)

    return ChatResponse(reply=result.reply, products=result.products or None)


@app.get("/api/chat/history", response_model=list[ChatHistoryEntry])
def chat_history(user_id: int):
    """A logged-in customer's saved conversation, oldest first — the frontend
    calls this on login/page load to reload where they left off. Guests have
    no user_id and so never call this.
    """
    return get_chat_history(user_id)


@app.get("/api/health")
def health():
    return {"status": "ok"}
