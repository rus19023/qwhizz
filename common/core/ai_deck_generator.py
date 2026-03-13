# core/ai_deck_generator.py
"""
AI-powered deck generation from various source types:
  - PDF files
  - Word documents (.docx)
  - Plain text files (.txt)
  - Web page URLs

Calls Claude API to extract and structure flashcards, then returns
a list of card dicts ready for preview and import.
"""

from __future__ import annotations
import json
import requests
import streamlit as st


# ── Source extractors ─────────────────────────────────────────────────────────

def _extract_text_from_pdf(file) -> str:
    try:
        import pdfplumber
        with pdfplumber.open(file) as pdf:
            return "\n\n".join(
                page.extract_text() or "" for page in pdf.pages
            ).strip()
    except ImportError:
        st.error("pdfplumber not installed. Run: pip install pdfplumber")
        return ""


def _extract_text_from_docx(file) -> str:
    try:
        from docx import Document
        import io
        doc = Document(io.BytesIO(file.read()))
        return "\n\n".join(para.text for para in doc.paragraphs if para.text.strip())
    except ImportError:
        st.error("python-docx not installed. Run: pip install python-docx")
        return ""


def _extract_text_from_url(url: str) -> str:
    try:
        from bs4 import BeautifulSoup
        response = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        return soup.get_text(separator="\n").strip()
    except ImportError:
        st.error("beautifulsoup4 not installed. Run: pip install beautifulsoup4 requests")
        return ""
    except Exception as e:
        st.error(f"Could not fetch URL: {e}")
        return ""


# ── Claude API call ───────────────────────────────────────────────────────────

def _get_headers() -> dict:
    try:
        api_key = st.secrets["ANTHROPIC_API_KEY"]
    except Exception:
        import toml, os
        secrets_path = os.path.join(
            os.path.dirname(__file__), "..", ".streamlit", "secrets.toml"
        )
        api_key = toml.load(secrets_path)["ANTHROPIC_API_KEY"]
    return {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
    }


SYSTEM_PROMPT = """You are an expert educator creating flashcard decks from study materials.
Analyze the provided text and generate high-quality flashcards.

Return ONLY a valid JSON array of card objects. Each card must have:
- "question": clear, specific question
- "answer": concise but complete answer
- "type": one of "flashcard", "true_false", or "multiple_choice"

For true_false cards, also include:
- "correct_answer": true or false (boolean)

For multiple_choice cards, also include:
- "options": array of 4 answer strings (include the correct answer in the array)
- "correct_index": index of the correct answer in options (0-3)

Guidelines:
- Create a mix of card types when appropriate
- Focus on key concepts, definitions, and facts
- Make questions clear and unambiguous
- Keep answers concise but complete
- Aim for 10-25 cards depending on content length
- Do NOT include any text outside the JSON array"""


def generate_cards_from_text(text: str, num_cards: int = 15) -> list[dict]:
    """
    Send extracted text to Claude and return a list of card dicts.
    Returns [] on any failure.
    """
    if not text.strip():
        return []

    # Truncate very long texts to avoid token limits
    max_chars = 12000
    if len(text) > max_chars:
        text = text[:max_chars] + "\n\n[Text truncated for length]"

    prompt = (
        f"Generate approximately {num_cards} flashcards from the following study material.\n\n"
        f"---\n{text}\n---\n\n"
        f"Return ONLY the JSON array, no other text."
    )

    try:
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=_get_headers(),
            json={
                "model": "claude-haiku-4-5-20251001",
                "max_tokens": 4000,
                "system": SYSTEM_PROMPT,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=60,
        )
        response.raise_for_status()
        raw = response.json()["content"][0]["text"].strip()

        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1].lstrip("json").strip()
            if "```" in raw:
                raw = raw[: raw.index("```")]

        cards = json.loads(raw)
        if isinstance(cards, list):
            return cards
    except json.JSONDecodeError as e:
        st.error(f"AI returned invalid JSON: {e}")
    except Exception as e:
        st.error(f"AI generation failed: {e}")

    return []


# ── Main entry points ─────────────────────────────────────────────────────────

def generate_from_file(uploaded_file, num_cards: int = 15) -> tuple[str, list[dict]]:
    """
    Extract text from an uploaded file and generate cards.
    Returns (extracted_text, cards).
    """
    name = uploaded_file.name.lower()
    text = ""

    if name.endswith(".pdf"):
        text = _extract_text_from_pdf(uploaded_file)
    elif name.endswith(".docx"):
        text = _extract_text_from_docx(uploaded_file)
    elif name.endswith(".txt"):
        text = uploaded_file.read().decode("utf-8", errors="ignore")
    else:
        st.error(f"Unsupported file type: {name}")

    if not text:
        return "", []

    cards = generate_cards_from_text(text, num_cards)
    return text, cards


def generate_from_url(url: str, num_cards: int = 15) -> tuple[str, list[dict]]:
    """
    Fetch a URL, extract text, and generate cards.
    Returns (extracted_text, cards).
    """
    text = _extract_text_from_url(url)
    if not text:
        return "", []
    cards = generate_cards_from_text(text, num_cards)
    return text, cards


def generate_from_text(raw_text: str, num_cards: int = 15) -> tuple[str, list[dict]]:
    """
    Generate cards directly from pasted text.
    Returns (raw_text, cards).
    """
    cards = generate_cards_from_text(raw_text, num_cards)
    return raw_text, cards