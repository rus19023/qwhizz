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
import logging
import requests
import streamlit as st
from core.prompt import SYSTEM_PROMPT

logging.getLogger("pdfplumber").setLevel(logging.ERROR)


# ── Provider registry ─────────────────────────────────────────────────────────

PROVIDERS = {
    "Ollama (Local)":     "ollama",
    "Claude (Anthropic)": "claude",
    "OpenAI":             "openai",
}

# Default models per provider
DEFAULT_MODELS = {
    "claude": "claude-haiku-4-5-20251001",
    "openai": "gpt-4o-mini",
    "ollama": "mistral:latest",
}


# ── Source extractors ─────────────────────────────────────────────────────────

def _extract_text_from_pdf(file) -> str:
    """
    Extract text from a PDF file using pdfplumber.
    Returns empty string for scanned/image PDFs — use OCR for those.

    Args:
        file: Uploaded file object.

    Returns:
        str: Extracted text, or empty string on failure.
    """
    try:
        import pdfplumber
        with pdfplumber.open(file) as pdf:
            pages = [page.extract_text() or "" for page in pdf.pages]
        text = "\n\n".join(pages).strip()
        if not text:
            st.warning(
                f"No text extracted from {getattr(file, 'name', 'file')}. "
                "This may be a scanned/image PDF — try copying the text manually "
                "and using the 'Paste text' option instead."
            )
        return text
    except ImportError:
        st.error("pdfplumber not installed. Run: pip install pdfplumber")
        return ""
    except Exception as e:
        st.error(f"PDF extraction failed: {e}")
        return ""


def _extract_text_from_docx(file) -> str:
    """
    Extract text from a Word document.

    Args:
        file: Uploaded file object.

    Returns:
        str: Extracted text, or empty string on failure.
    """
    try:
        from docx import Document
        import io
        doc = Document(io.BytesIO(file.read()))
        return "\n\n".join(para.text for para in doc.paragraphs if para.text.strip())
    except ImportError:
        st.error("python-docx not installed. Run: pip install python-docx")
        return ""
    except Exception as e:
        st.error(f"DOCX extraction failed: {e}")
        return ""


def _extract_text_from_url(url: str) -> str:
    """
    Fetch and extract readable text from a web page.

    Args:
        url (str): The URL to fetch.

    Returns:
        str: Extracted text, or empty string on failure.
    """
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
    """
    Fetch a secret from st.secrets or fall back to secrets.toml.

    Args:
        key (str): Secret key name.

    Returns:
        str | None: Secret value, or None if not found.
    """
    try:
        return st.secrets[key]
    except Exception:
        try:
            import toml
            import os
            secrets_path = os.path.join(
                os.path.dirname(__file__), "..", ".streamlit", "secrets.toml"
            )
            return toml.load(secrets_path).get(key)
        except Exception:
            return None


# ── Provider: Claude ──────────────────────────────────────────────────────────

def _call_claude(prompt: str, model: str) -> str:
    """
    Call the Anthropic Claude API.

    Args:
        prompt (str): User prompt text.
        model (str): Claude model name.

    Returns:
        str: Response text, or empty string on failure.
    """
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
    """
    Call the OpenAI chat completions API.

    Args:
        prompt (str): User prompt text.
        model (str): OpenAI model name.

    Returns:
        str: Response text, or empty string on failure.
    """
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
            "max_tokens": 6000,
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
    """
    Call a locally running Ollama model.

    Args:
        prompt (str): User prompt text.
        model (str): Ollama model name (e.g. 'mistral:latest').

    Returns:
        str: Response text, or empty string on failure.
    """
    base_url = _get_secret("OLLAMA_BASE_URL") or "http://localhost:11434"

    # Verify Ollama is reachable before attempting generation
    try:
        health = requests.get(f"{base_url}/api/tags", timeout=5)
        health.raise_for_status()
        available_models = [m["name"] for m in health.json().get("models", [])]
        if model not in available_models:
            st.warning(
                f"Model '{model}' not found. "
                f"Available: {', '.join(available_models)}"
            )
    except Exception as e:
        st.error(f"Cannot reach Ollama at {base_url}: {e}")
        return ""

    try:
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
            timeout=300,  # local models can be slow on CPU
        )
        response.raise_for_status()
        return response.json()["message"]["content"].strip()
    except requests.exceptions.Timeout:
        st.error(
            f"Timed out after 300s — prompt was {len(prompt)} chars on model '{model}'. "
            "Try reducing the number of cards or using a smaller model."
        )
    except Exception as e:
        st.error(f"Ollama error: {type(e).__name__}: {e}")
    return ""


# ── Prompt builder ────────────────────────────────────────────────────────────

def _build_prompt(text: str, num_cards: int) -> str:
    """
    Build the user prompt for card generation.

    Args:
        text (str): Extracted source text.
        num_cards (int): Approximate number of cards to request.

    Returns:
        str: Formatted prompt string.
    """
    return (
        f"Generate approximately {num_cards} flashcards from the following study material.\n\n"
        f"---\n{text}\n---\n\n"
        f"Return ONLY the JSON array, no other text."
    )


# ── Dispatcher ────────────────────────────────────────────────────────────────

def _call_provider(prompt: str, provider: str, model: str) -> str:
    """
    Route to the correct provider backend.

    Args:
        prompt (str): The prompt to send.
        provider (str): Provider key — 'claude', 'openai', or 'ollama'.
        model (str): Model name.

    Returns:
        str: Raw response text, or empty string on failure.
    """
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
    """
    Strip markdown fences and parse a JSON array from the AI response.

    Args:
        raw (str): Raw response text from the AI.

    Returns:
        list[dict]: Parsed card dicts, or empty list on failure.
    """
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

    Args:
        text (str): Source text to generate cards from.
        num_cards (int): Approximate number of cards to generate.
        provider (str): Provider key.
        model (str | None): Model override. Falls back to DEFAULT_MODELS[provider].

    Returns:
        list[dict]: Generated card dicts, or empty list on any failure.
    """
    if not text.strip():
        return []

    model = model or DEFAULT_MODELS.get(provider, DEFAULT_MODELS["claude"])

    # Ollama on CPU is much slower — use a smaller context window
    max_chars = 4000 if provider == "ollama" else 12000
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
    uploaded_files,
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
    """
    Fetch a web page and generate cards from its text content.

    Args:
        url (str): The URL to fetch.
        num_cards (int): Approximate number of cards to generate.
        provider (str): AI provider key.
        model (str | None): Model override.

    Returns:
        tuple[str, list[dict]]: (extracted_text, generated_cards)
    """
    text = _extract_text_from_url(url)
    if not text:
        return "", []
    cards = generate_cards_from_text(text, num_cards, provider, model)
    return text, cards


def generate_from_text(
    raw_text: str,
    num_cards: int = 15,
    provider: str = "ollama",
    model: str | None = None,
) -> tuple[str, list[dict]]:
    """
    Generate cards directly from pasted/provided text.

    Args:
        raw_text (str): The source text.
        num_cards (int): Approximate number of cards to generate.
        provider (str): AI provider key.
        model (str | None): Model override.

    Returns:
        tuple[str, list[dict]]: (raw_text, generated_cards)
    """
    cards = generate_cards_from_text(raw_text, num_cards, provider, model)
    return raw_text, cards