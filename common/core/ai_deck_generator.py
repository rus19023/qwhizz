# core/ai_deck_generator.py
"""
AI-powered deck generation from various source types:
  - PDF files
  - Word documents (.docx)
  - Plain text files (.txt)
  - Web page URLs

Supports multiple AI providers:
  - Claude (Anthropic)
  - OpenAI (GPT-4o, etc.)
  - Ollama (local models)
"""

from __future__ import annotations
import json
import requests
import streamlit as st
from core.prompt import SYSTEM_PROMPT


# ── Provider registry ─────────────────────────────────────────────────────────

PROVIDERS = {
    "Claude (Anthropic)": "claude",
    "OpenAI":             "openai",
    "Ollama (Local)":     "ollama",
}

# Default models per provider
DEFAULT_MODELS = {
    "claude": "claude-haiku-4-5-20251001",
    "openai": "gpt-4o-mini",
    "ollama": "llama3.2",
}


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


# ── Secret helpers ────────────────────────────────────────────────────────────

def _get_secret(key: str) -> str | None:
    """Fetch a secret from st.secrets or fallback to secrets.toml."""
    try:
        return st.secrets[key]
    except Exception:
        try:
            import toml, os
            secrets_path = os.path.join(
                os.path.dirname(__file__), "..", ".streamlit", "secrets.toml"
            )
            return toml.load(secrets_path).get(key)
        except Exception:
            return None


# ── Provider: Claude ──────────────────────────────────────────────────────────

def _call_claude(prompt: str, model: str) -> str:
    api_key = _get_secret("ANTHROPIC_API_KEY")
    if not api_key:
        st.error("ANTHROPIC_API_KEY not found in secrets.")
        return ""

    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        json={
            "model": model,
            "max_tokens": 4000,
            "system": SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=60,
    )
    response.raise_for_status()
    return response.json()["content"][0]["text"].strip()


# ── Provider: OpenAI ──────────────────────────────────────────────────────────

def _call_openai(prompt: str, model: str) -> str:
    api_key = _get_secret("OPENAI_API_KEY")
    if not api_key:
        st.error("OPENAI_API_KEY not found in secrets.")
        return ""

    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        json={
            "model": model,
            "max_tokens": 4000,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": prompt},
            ],
        },
        timeout=60,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"].strip()


# ── Provider: Ollama ──────────────────────────────────────────────────────────

def _call_ollama(prompt: str, model: str) -> str:
    base_url = _get_secret("OLLAMA_BASE_URL") or "http://localhost:11434"

    response = requests.post(
        f"{base_url}/api/chat",
        json={
            "model": model,
            "stream": False,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": prompt},
            ],
        },
        timeout=120,  # local models can be slow
    )
    response.raise_for_status()
    return response.json()["message"]["content"].strip()


def _build_prompt(text: str, num_cards: int) -> str:
    return (
        f"Generate approximately {num_cards} flashcards from the following study material.\n\n"
        f"---\n{text}\n---\n\n"
        f"Return ONLY the JSON array, no other text."
    )


# ── Dispatcher ────────────────────────────────────────────────────────────────

def _call_provider(prompt: str, provider: str, model: str) -> str:
    """Route to the correct provider backend."""
    if provider == "claude":
        return _call_claude(prompt, model)
    elif provider == "openai":
        return _call_openai(prompt, model)
    elif provider == "ollama":
        return _call_ollama(prompt, model)
    else:
        st.error(f"Unknown provider: {provider}")
        return ""


def _parse_response(raw: str) -> list[dict]:
    """Strip markdown fences and parse JSON."""
    if raw.startswith("```"):
        raw = raw.split("```")[1].lstrip("json").strip()
        if "```" in raw:
            raw = raw[: raw.index("```")]
    cards = json.loads(raw)
    if isinstance(cards, list):
        return cards
    return []


# ── Core generation function ──────────────────────────────────────────────────

def generate_cards_from_text(
    text: str,
    num_cards: int = 15,
    provider: str = "claude",
    model: str | None = None,
) -> list[dict]:
    """
    Send extracted text to the selected AI provider and return card dicts.
    Returns [] on any failure.
    """
    if not text.strip():
        return []

    model = model or DEFAULT_MODELS.get(provider, DEFAULT_MODELS["claude"])

    # Truncate very long texts
    max_chars = 12000
    if len(text) > max_chars:
        text = text[:max_chars] + "\n\n[Text truncated for length]"

    prompt = _build_prompt(text, num_cards)

    try:
        raw = _call_provider(prompt, provider, model)
        if not raw:
            return []
        return _parse_response(raw)
    except json.JSONDecodeError as e:
        st.error(f"AI returned invalid JSON: {e}")
    except Exception as e:
        st.error(f"AI generation failed ({provider}): {e}")

    return []


# ── Main entry points ─────────────────────────────────────────────────────────

def generate_from_file(
    uploaded_files,                    # now a list
    num_cards: int = 15,
    provider: str = "claude",
    model: str | None = None,
) -> tuple[str, list[dict]]:
    """
    Extract text from one or more uploaded files, concatenate, and generate cards.
    Supports .pdf, .docx, and .txt files in any combination.

    Args:
        uploaded_files: A single file or list of files from st.file_uploader.
        num_cards (int): Approximate number of cards to generate.
        provider (str): AI provider key.
        model (str | None): Model override.

    Returns:
        tuple[str, list[dict]]: (concatenated_text, generated_cards)
    """
    # Normalise to list so callers can pass a single file or a list
    if not isinstance(uploaded_files, list):
        uploaded_files = [uploaded_files]

    texts = []
    for uploaded_file in uploaded_files:
        name = uploaded_file.name.lower()
        if name.endswith(".pdf"):
            text = _extract_text_from_pdf(uploaded_file)
        elif name.endswith(".docx"):
            text = _extract_text_from_docx(uploaded_file)
        elif name.endswith(".txt"):
            text = uploaded_file.read().decode("utf-8", errors="ignore")
        else:
            st.warning(f"Skipping unsupported file type: {uploaded_file.name}")
            continue

        if text.strip():
            # Label each source so the AI knows where content came from
            texts.append(f"=== Source: {uploaded_file.name} ===\n{text}")
        else:
            st.warning(f"No text extracted from {uploaded_file.name}")

    if not texts:
        return "", []

    combined = "\n\n".join(texts)
    cards = generate_cards_from_text(combined, num_cards, provider, model)
    return combined, cards


def generate_from_url(
    url: str,
    num_cards: int = 15,
    provider: str = "claude",
    model: str | None = None,
) -> tuple[str, list[dict]]:
    text = _extract_text_from_url(url)
    if not text:
        return "", []
    cards = generate_cards_from_text(text, num_cards, provider, model)
    return text, cards


def generate_from_text(
    raw_text: str,
    num_cards: int = 15,
    provider: str = "claude",
    model: str | None = None,
) -> tuple[str, list[dict]]:
    cards = generate_cards_from_text(raw_text, num_cards, provider, model)
    return raw_text, cards

