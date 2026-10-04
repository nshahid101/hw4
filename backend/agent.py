"""Pydantic AI agent behind POST /api/chat.

main.py imports run_agent from this module. Keep that signature stable.

Tools (tools.py): search_products (semantic catalogue search, for browsing)
and get_product_info (grounded DB lookup of description/price/stock-by-size
for one product). Two more tools are defined here, not tools.py, because
they don't read the catalogue — they read this one run's context (the
"agent context" mentioned in the customer-memory requirement), passed in via
pydantic_ai's RunContext/deps mechanism rather than a database query:

- get_current_customer: who is chatting (from ChatDeps.user, set by main.py
  from the logged-in user_id — None for a guest).
- get_current_page: what page/product the customer is looking at right now
  (from ChatDeps.page, set by main.py from what the frontend sent), so the
  agent can resolve "do you have this in pink?" on a product detail page.

System prompt: prompts/prompt.md.

Every run also appends one entry to output/audit_trail.json (time, the
customer's message, each tool call with its args/result, the stop reason,
and the reply) via _append_audit/_trace below. That file is append-only —
it is read, added to, and rewritten whole each time, never truncated or
cleared, so it keeps a full history across every server restart.
"""

from __future__ import annotations

import json
import os
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic_ai import Agent, RunContext
from pydantic_ai.messages import ModelResponse, NativeToolCallPart, ToolCallPart, ToolReturnPart
from pydantic_ai.models.openai import OpenAIResponsesModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.usage import UsageLimits

from models import AgentResult, CustomerInfo, PageContext, Product
from tools import get_product
from tools import get_product_info as get_product_info_impl
from tools import search_products as search_products_impl

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

# The .env may sit in HW 4/ or one level up (AI Foundations/.env). Load both.
load_dotenv(ROOT / ".env")
load_dotenv(ROOT.parent / ".env")

MODEL_NAME = "gpt-5-6luna"
# A normal reply needs at most 1-2 tool calls; capping well above that still
# leaves room for a multi-step question (search, then a size/stock lookup)
# while stopping a runaway tool loop from ever running unbounded.
MAX_MODEL_REQUESTS = 10
PORTKEY_BASE_URL = os.getenv("PORTKEY_BASE_URL", "https://api.portkey.ai/v1").rstrip("/")
PROMPT_PATH = HERE / "prompts" / "prompt.md"
AUDIT_PATH = ROOT / "output" / "audit_trail.json"
_audit_lock = threading.Lock()


@dataclass
class ChatDeps:
    """This run's context, passed to agent.run_sync(..., deps=...) and read
    by tools via RunContext[ChatDeps].deps. Neither field is ever guessed —
    both are set by main.py from real request data (the logged-in user_id,
    if any, and whatever page the frontend says the customer is on).
    """

    user: CustomerInfo | None
    page: PageContext | None


def _system_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def _build_agent(tools_used: list[str], collected_products: dict[str, Product]) -> Agent:
    """Wire the model and the four tools; tools_used/collected_products are
    filled in as a side channel so run_agent can report what happened and
    surface matched products alongside the reply, without needing structured
    output from the model itself.
    """
    key = os.getenv("PORTKEY_API_KEY", "").strip()
    if not key:
        raise RuntimeError("PORTKEY_API_KEY is not set (add it to a .env file).")

    client = AsyncOpenAI(
        api_key=key,
        base_url=PORTKEY_BASE_URL,
        default_headers={"x-portkey-api-key": key},
    )
    model = OpenAIResponsesModel(MODEL_NAME, provider=OpenAIProvider(openai_client=client))
    agent = Agent(model, instructions=_system_prompt(), deps_type=ChatDeps)

    @agent.tool
    def search_products(ctx: RunContext[ChatDeps], query: str, limit: int = 8) -> dict:
        """Search the Campus Customs catalogue by meaning (garment type, sport, college, color, occasion)."""
        if "search_products" not in tools_used:
            tools_used.append("search_products")
        result = search_products_impl(query, limit)
        for product in result.products:
            collected_products[product.product_id] = product
        return result.model_dump()

    @agent.tool
    def get_product_info(ctx: RunContext[ChatDeps], identifier: str, size: str | None = None) -> dict:
        """Look up the real description, price, and stock-by-size for one product, by product_id or name."""
        if "get_product_info" not in tools_used:
            tools_used.append("get_product_info")
        result = get_product_info_impl(identifier, size)
        if result.found:
            product = get_product(result.product_id)
            if product is not None:
                collected_products[product.product_id] = product
        return result.model_dump()

    @agent.tool
    def get_current_customer(ctx: RunContext[ChatDeps]) -> dict:
        """Return the name/email of the customer currently chatting, or note that they're a guest."""
        if "get_current_customer" not in tools_used:
            tools_used.append("get_current_customer")
        user = ctx.deps.user
        if user is None:
            return {"logged_in": False, "note": "This customer is browsing as a guest — no name/email on file."}
        return {
            "logged_in": True,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "name": user.name,
            "email": user.email,
        }

    @agent.tool
    def get_current_page(ctx: RunContext[ChatDeps]) -> dict:
        """Return what page the customer is on right now — call this to figure out what "this"/"it" refers to."""
        if "get_current_page" not in tools_used:
            tools_used.append("get_current_page")
        page = ctx.deps.page
        if page is None:
            return {"known": False, "note": "The current page wasn't reported."}
        if page.page != "product_detail" or not page.product_id:
            return {"known": True, "page": page.page, "viewing_product": False}
        return {
            "known": True,
            "page": page.page,
            "viewing_product": True,
            "product_id": page.product_id,
            "note": "Call get_product_info with this product_id to get its current price/colors/sizes.",
        }

    return agent


def _shorten(value: Any, limit: int = 400) -> str:
    """Compact a value to a short, single-line string for the audit log —
    args/results can be long (a full product dict), and the log should stay
    skimmable rather than storing the entire payload every time.
    """
    try:
        text = value if isinstance(value, str) else json.dumps(value, default=str)
    except Exception:
        text = str(value)
    text = " ".join(text.split())
    return text if len(text) <= limit else text[:limit].rstrip() + "...[truncated]"


def _trace(messages: list[Any]) -> tuple[list[dict], str]:
    """Pull a short {tool, args, result} entry per tool call, plus the
    model's stop reason, out of one agent run's full message history.
    """
    calls_by_id: dict[str, dict] = {}
    ordered: list[dict] = []
    stop_reason = "unknown"

    for message in messages:
        if isinstance(message, ModelResponse):
            if message.finish_reason:
                stop_reason = str(message.finish_reason)
            for part in message.parts:
                if isinstance(part, NativeToolCallPart):
                    ordered.append(
                        {
                            "tool": part.tool_name or "native_tool",
                            "args": _shorten(part.args),
                            "result": "(ran server-side)",
                        }
                    )
                elif isinstance(part, ToolCallPart):
                    entry = {"tool": part.tool_name, "args": _shorten(part.args), "result": ""}
                    calls_by_id[part.tool_call_id] = entry
                    ordered.append(entry)
        else:
            for part in getattr(message, "parts", []):
                if isinstance(part, ToolReturnPart):
                    entry = calls_by_id.get(part.tool_call_id)
                    if entry is not None:
                        entry["result"] = _shorten(part.content)

    return ordered, stop_reason


def _append_audit(entry: dict) -> None:
    """Append one run to output/audit_trail.json. Append-only: reads whatever
    is already there, adds this entry to the end, and writes the whole list
    back — existing entries are never cleared or overwritten between runs,
    and this survives server restarts since it's just a file on disk.
    """
    with _audit_lock:
        AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
        rows: list[Any] = []
        if AUDIT_PATH.exists() and AUDIT_PATH.stat().st_size > 0:
            try:
                existing = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
                rows = existing if isinstance(existing, list) else [existing]
            except json.JSONDecodeError:
                # Corrupt file: preserve it under a new name rather than
                # silently discarding whatever was in it, then start fresh.
                stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
                AUDIT_PATH.replace(AUDIT_PATH.with_name(f"audit_trail.corrupt-{stamp}.json"))
        rows.append(entry)
        tmp = AUDIT_PATH.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(AUDIT_PATH)


def run_agent(
    message: str, user: CustomerInfo | None = None, page: PageContext | None = None
) -> dict:
    """Run one agent turn. Returns an AgentResult dict: reply, products, tools_used."""
    tools_used: list[str] = []
    collected_products: dict[str, Product] = {}
    started = datetime.now(timezone.utc).isoformat(timespec="seconds")

    try:
        agent = _build_agent(tools_used, collected_products)
        result = agent.run_sync(
            message,
            deps=ChatDeps(user=user, page=page),
            usage_limits=UsageLimits(request_limit=MAX_MODEL_REQUESTS),
        )
        reply = str(result.output)
        tool_calls, stop_reason = _trace(list(result.all_messages()))
    except Exception as exc:
        reply = f"Sorry, I ran into an error answering that: {type(exc).__name__}: {exc}"
        tool_calls, stop_reason = [], f"error: {type(exc).__name__}: {exc}"

    _append_audit(
        {
            "time": started,
            "user_message": _shorten(message, 300),
            "tool_calls": tool_calls,
            "stop_reason": stop_reason,
            "reply": _shorten(reply, 500),
        }
    )

    return AgentResult(
        reply=reply,
        products=list(collected_products.values()),
        tools_used=tools_used,
    ).model_dump()
