"""
common/quizforge/importer.py — QWhizz-side FastAPI receiver for QuizForge.

Spins up a FastAPI server in a background thread when imported.
Drop this into any QWhizz app that wants to receive cards from QuizForge.

Usage in a QWhizz app's runapp.py:
    from quizforge.importer import start_import_server
    start_import_server()

Then in secrets.toml:
    [quizforge]
    port = 8502
"""

import threading
from datetime import datetime, timezone
from typing import Any

import streamlit as st

# ── Lazy imports (only needed when server starts) ─────────────────────────────

def _get_port() -> int:
    try:
        return int(st.secrets.get("quizforge", {}).get("port", 8502))
    except Exception:
        return 8502


_server_started = False
_server_lock    = threading.Lock()


def start_import_server() -> None:
    """Start the FastAPI import server in a background thread (idempotent)."""
    global _server_started
    with _server_lock:
        if _server_started:
            return
        _server_started = True

    port = _get_port()
    thread = threading.Thread(
        target=_run_server,
        args=(port,),
        daemon=True,
        name="quizforge-import-server",
    )
    thread.start()


def _run_server(port: int) -> None:
    import uvicorn
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel

    app = FastAPI(title="QWhizz Import API", version="1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    # ── Request / response models ─────────────────────────────────────────────

    class ImportRequest(BaseModel):
        deck_name: str
        cards: list[dict]
        source: str = "quizforge"

    class ImportResponse(BaseModel):
        imported: int
        deck_name: str
        deck_created: bool
        message: str

    # ── Routes ────────────────────────────────────────────────────────────────

    @app.get("/api/health")
    def health() -> dict:
        return {"status": "ok", "service": "qwhizz-import"}

    @app.post("/api/import", response_model=ImportResponse)
    def import_cards(req: ImportRequest) -> ImportResponse:
        """Receive cards from QuizForge and insert into MongoDB."""
        from data.db import get_db

        db         = get_db()
        decks_col  = db["decks"]
        now        = datetime.now(timezone.utc)

        # ── Find or create deck ───────────────────────────────────────────────
        deck = decks_col.find_one({"name": req.deck_name})
        created = False

        if not deck:
            deck = {
                "name":        req.deck_name,
                "description": f"Imported from {req.source}",
                "cards":       [],
                "created_at":  now,
                "updated_at":  now,
                "source":      req.source,
            }
            result   = decks_col.insert_one(deck)
            deck["_id"] = result.inserted_id
            created  = True

        # ── Prepare cards ─────────────────────────────────────────────────────
        prepared = [_prepare_card(c, req.source, now) for c in req.cards]

        # ── Push cards into deck ──────────────────────────────────────────────
        decks_col.update_one(
            {"_id": deck["_id"]},
            {
                "$push":  {"cards": {"$each": prepared}},
                "$set":   {"updated_at": now},
            },
        )

        return ImportResponse(
            imported=len(prepared),
            deck_name=req.deck_name,
            deck_created=created,
            message=(
                f"Created deck '{req.deck_name}' and imported {len(prepared)} cards"
                if created
                else f"Added {len(prepared)} cards to existing deck '{req.deck_name}'"
            ),
        )

    # ── Start server ──────────────────────────────────────────────────────────
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning")


def _prepare_card(raw: dict, source: str, now: datetime) -> dict:
    """Normalize a raw card dict to match QWhizz's Card schema."""
    feedback = raw.get("feedback", {})
    if not isinstance(feedback, dict):
        feedback = {}

    return {
        "question":     str(raw.get("question", "")).strip(),
        "answer":       str(raw.get("answer", "")).strip(),
        "wrong_answers": [str(w) for w in raw.get("wrong_answers", [])],
        "hint":         str(raw.get("hint", "") or ""),
        "tags":         [str(t) for t in raw.get("tags", [])] + [source],
        "image_url":    raw.get("image_url", ""),
        "explanation":  str(raw.get("explanation", "") or ""),
        "feedback": {
            "text":   str(feedback.get("text", "") or ""),
            "images": feedback.get("images", []),
            "links":  feedback.get("links", []),
        },
        "type":         raw.get("type", "flashcard"),
        "imported_at":  now,
        "source":       source,
    }