# Campus Customs — HW4

A customer-facing website for Campus Customs (a Yale-merch shop) with a React + Vite +
TypeScript frontend and a FastAPI backend that runs a Pydantic AI shopping assistant.

## Project layout

```
HW4/
├── AI_prompts.md       # log of prompts used while building this
├── requirements.txt    # backend Python dependencies
├── .env.example        # copy to .env and fill in your real key
├── README.md
├── frontend/           # Vite + React + TypeScript app
├── backend/
│   ├── main.py         # FastAPI app — run with: uvicorn main:app --reload --port 8000
│   ├── agent.py        # Pydantic AI agent (tools, model, audit logging)
│   ├── models.py       # shared Pydantic models
│   ├── tools.py        # catalogue/DB access + agent tools
│   └── prompts/
│       └── prompt.md   # the agent's system prompt
└── output/             # assignment write-ups, screenshots, audit log
```

Not included in this repo (see **Getting the data** below):

```
data/
├── campus_customs.db   # SQLite database (catalogue, inventory, users, chat history)
└── products/           # product photos referenced by the catalogue
```

## Prerequisites

- Python 3.11+
- Node.js 18+ and npm

## Getting the data

This repo doesn't include the database or product photos (they're real data files, not
source code). Before running the backend, get the `data/` folder (containing
`campus_customs.db` and `products/`) from the course materials and place it at the root
of this project, so you end up with `HW4/data/campus_customs.db` and
`HW4/data/products/`.

## 1. Configure your API key

```bash
cp .env.example .env
```

Edit `.env` and set `PORTKEY_API_KEY` to your real Portkey API key. This is required for
the chat assistant (`Ask the Bulldog`) to work — the rest of the site (browsing products,
creating an account, logging in) works without it.

## 2. Run the backend

From the project root:

```bash
python3 -m venv backend/.venv
backend/.venv/Scripts/activate    # Windows
# source backend/.venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
cd backend
uvicorn main:app --reload --port 8000
```

The API is now running at `http://localhost:8000` (interactive docs at `/docs`).

## 3. Run the frontend

In a second terminal, from the project root:

```bash
cd frontend
npm install
npm run dev
```

The site is now running at `http://localhost:5173`. Both the backend (port 8000) and the
frontend (port 5173) need to be running at the same time — the frontend talks directly
to the backend over HTTP.

## Notes

- The seeded test account is `test@campuscustoms.yale.edu` / `password`.
- `output/` contains the write-ups produced while building this (`harness.md`,
  `usability.md`, `design.md`), a live app-check report (`app_check.html` +
  `app_check_images/`), and the agent's append-only activity log (`audit_trail.json`).
