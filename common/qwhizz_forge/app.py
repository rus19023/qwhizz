"""
common/qwhizz_forge/app.py — QWhizz Forge: Bloom's-aligned deck generator.

A shared tab that any QWhizz app can embed via:
    from qwhizz_forge.app import render_forge_tab

Register it in qwhizz.py like any other tab:
    TabSpec("🔨 Forge", lambda: render_forge_tab(current_deck, username))
"""

import json
import re
from collections import Counter
from urllib.parse import urlparse

import requests
import streamlit as st

# ── Config (read from whichever app's secrets.toml is loaded) ─────────────────
def _cfg(key: str, default: str) -> str:
    return st.secrets.get("qwhizz_forge", {}).get(key, default)

OLLAMA_BASE    = _cfg("ollama_url",    "http://localhost:11434")
QWHIZZ_API_URL = _cfg("qwhizz_url",   "http://localhost:8502")
DEFAULT_MODEL  = _cfg("default_model", "llama3")
MAX_CARDS      = 30

CARD_TYPES        = ["flashcard", "multiple_choice", "true_false"]
DIFFICULTY_LEVELS = ["easy", "medium", "hard", "mixed"]

# ── URL allowlist — only fetch from public internet, never internal IPs ───────
_BLOCKED_HOSTS = re.compile(
    r"^(localhost|127\.|10\.|172\.(1[6-9]|2[0-9]|3[01])\.|192\.168\.|0\.0\.0\.0|::1|fd[0-9a-f]{2}:)",
    re.IGNORECASE,
)
_MAX_TOPIC_LEN       = 200
_MAX_DECK_NAME_LEN   = 100
_MAX_SOURCE_LEN      = 8000
_TOPIC_STRIP_PATTERN = re.compile(r"[^\w\s,.\-:()'\"/]", re.UNICODE)

# ── Bloom's Taxonomy ──────────────────────────────────────────────────────────
BLOOM_LEVELS: dict[str, dict] = {
    "Remember":   {"description": "Recall facts and basic concepts",        "verbs": "define, list, recall, recognize, repeat, state",       "icon": "1️⃣", "color": "#6c757d", "points": 1},
    "Understand": {"description": "Explain ideas in your own words",        "verbs": "classify, describe, explain, summarize, interpret",     "icon": "2️⃣", "color": "#0d6efd", "points": 2},
    "Apply":      {"description": "Use information in new situations",      "verbs": "calculate, demonstrate, solve, use, implement",         "icon": "3️⃣", "color": "#198754", "points": 3},
    "Analyze":    {"description": "Draw connections and break down info",   "verbs": "compare, contrast, differentiate, examine, break down", "icon": "4️⃣", "color": "#fd7e14", "points": 4},
    "Evaluate":   {"description": "Justify a decision or course of action", "verbs": "argue, defend, judge, critique, assess, justify",       "icon": "5️⃣", "color": "#dc3545", "points": 5},
    "Create":     {"description": "Produce new or original work",           "verbs": "design, construct, develop, formulate, compose, plan",  "icon": "6️⃣", "color": "#6f42c1", "points": 5},
    "Mixed":      {"description": "Distribute across all Bloom's levels",   "verbs": "all levels",                                           "icon": "🔀", "color": "#20c997", "points": 3},
}

# ── Input sanitization ────────────────────────────────────────────────────────

def _sanitize_topic(raw: str) -> str:
    """
    Strip characters that could be used for prompt injection.
    Keeps letters, numbers, spaces, and common punctuation.
    Caps length to prevent oversized prompts.
    """
    cleaned = _TOPIC_STRIP_PATTERN.sub("", raw).strip()
    return cleaned[:_MAX_TOPIC_LEN]


def _sanitize_deck_name(raw: str) -> str:
    """Strip anything that isn't a safe deck name character."""
    cleaned = re.sub(r"[^\w\s\-.()':]", "", raw).strip()
    return cleaned[:_MAX_DECK_NAME_LEN]


def _sanitize_source(raw: str) -> str:
    """Truncate source material to prevent oversized prompts."""
    return raw.strip()[:_MAX_SOURCE_LEN]


def _validate_url(url: str) -> tuple[bool, str]:
    """
    Reject URLs that point to internal/private network addresses (SSRF prevention).
    Only allows http/https schemes.
    Returns (is_valid, error_message).
    """
    try:
        parsed = urlparse(url)
    except Exception:
        return False, "Invalid URL format."

    if parsed.scheme not in ("http", "https"):
        return False, "Only http:// and https:// URLs are allowed."

    host = parsed.hostname or ""
    if not host:
        return False, "URL has no hostname."

    if _BLOCKED_HOSTS.match(host):
        return False, "URLs pointing to internal/private network addresses are not allowed."

    # Block raw IP addresses (public IPs could still be internal services)
    ip_pattern = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
    if ip_pattern.match(host):
        return False, "URLs with raw IP addresses are not allowed. Use a domain name."

    return True, ""


# ── Ollama helpers ────────────────────────────────────────────────────────────

def _ollama_available() -> bool:
    """Check if Ollama is reachable."""
    try:
        r = requests.get(f"{OLLAMA_BASE}/api/tags", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


def _get_models() -> list[str]:
    try:
        r = requests.get(f"{OLLAMA_BASE}/api/tags", timeout=5)
        if r.status_code == 200:
            return [m["name"] for m in r.json().get("models", [])]
    except Exception:
        pass
    return [DEFAULT_MODEL]


def _generate(
    model: str, topic: str, source_text: str,
    card_type: str, difficulty: str, bloom_level: str, num_cards: int,
) -> list[dict]:
    """Generate cards via Ollama. All inputs must already be sanitized."""

    # Validate enum inputs — never trust even selectbox values at the function level
    if card_type not in CARD_TYPES:
        st.error("Invalid card type.")
        return []
    if difficulty not in DIFFICULTY_LEVELS:
        st.error("Invalid difficulty.")
        return []
    if bloom_level not in BLOOM_LEVELS:
        st.error("Invalid Bloom's level.")
        return []
    if not (1 <= num_cards <= MAX_CARDS):
        st.error(f"Number of cards must be between 1 and {MAX_CARDS}.")
        return []
    if not topic:
        st.error("Topic cannot be empty.")
        return []

    type_instr = {
        "flashcard":       "Each card has a 'question' and an 'answer' (string).",
        "multiple_choice": "Each card has a 'question', an 'answer' (correct text), and 'wrong_answers' (list of 3 plausible incorrect options).",
        "true_false":      "Each card has a 'question' (declarative statement) and 'answer' which is exactly 'True' or 'False'.",
    }

    if bloom_level == "Mixed":
        bloom_instr = (
            "Distribute cards across ALL six Bloom's levels: "
            "Remember, Understand, Apply, Analyze, Evaluate, Create. "
            "Include 'bloom_level' on each card."
        )
    else:
        b = BLOOM_LEVELS[bloom_level]
        bloom_instr = (
            f"ALL cards target '{bloom_level}' — {b['description']}. "
            f"Use verbs: {b['verbs']}. "
            f"Set \"bloom_level\": \"{bloom_level}\" on every card."
        )

    source = f"\n\nSource material:\n{source_text}" if source_text else ""

    prompt = f"""You are an expert educational flashcard generator trained in Bloom's Taxonomy.

Generate exactly {num_cards} {difficulty} {card_type} cards about: {topic}

{type_instr[card_type]}

Bloom's requirement:
{bloom_instr}

Every card must also include:
- "hint": short memory aid (can be empty string)
- "tags": list of 1-3 topic tags
- "explanation": 1-2 sentence explanation shown after answering
- "bloom_level": one of Remember/Understand/Apply/Analyze/Evaluate/Create
- "estimated_time_seconds": integer 15-120
- "points": integer 1-5 based on cognitive complexity
{source}

Respond ONLY with a valid JSON array. No markdown, no preamble, no commentary."""

    try:
        r = requests.post(
            f"{OLLAMA_BASE}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=120,
        )
        r.raise_for_status()
        return _parse(r.json().get("response", ""))
    except requests.exceptions.ConnectionError:
        st.error(f"Cannot connect to Ollama at {OLLAMA_BASE}. Is it running?")
        return []
    except Exception as e:
        st.error(f"Ollama error: {e}")
        return []


def _parse(text: str) -> list[dict]:
    text  = re.sub(r"```(?:json)?", "", text).strip()
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if not match:
        st.error("Could not find JSON array in Ollama response.")
        st.code(text[:500], language="text")
        return []
    try:
        cards = json.loads(match.group())
        return [_normalize(c) for c in cards if isinstance(c, dict)]
    except json.JSONDecodeError as e:
        st.error(f"JSON parse error: {e}")
        return []


def _normalize(raw: dict) -> dict:
    """Sanitize and type-cast every field from raw Ollama output."""
    bloom = raw.get("bloom_level", "Remember")
    if bloom not in BLOOM_LEVELS or bloom == "Mixed":
        bloom = "Remember"

    # Clamp integers to safe ranges
    est_time = min(max(int(raw.get("estimated_time_seconds", 30)), 5), 300)
    points   = min(max(int(raw.get("points", BLOOM_LEVELS[bloom]["points"])), 1), 5)

    # All string fields cast and stripped — no raw HTML or special chars preserved
    return {
        "question":               str(raw.get("question", "")).strip()[:500],
        "answer":                 str(raw.get("answer",   "")).strip()[:500],
        "wrong_answers":          [str(w).strip()[:200] for w in raw.get("wrong_answers", [])[:6]],
        "hint":                   str(raw.get("hint",        "") or "").strip()[:200],
        "tags":                   [re.sub(r"[^\w\s\-]", "", str(t)).strip()[:50] for t in raw.get("tags", [])[:5]],
        "explanation":            str(raw.get("explanation", "") or "").strip()[:1000],
        "feedback":               {"text": "", "images": [], "links": []},
        "type":                   raw.get("type", "flashcard") if raw.get("type") in CARD_TYPES else "flashcard",
        "bloom_level":            bloom,
        "estimated_time_seconds": est_time,
        "points":                 points,
    }


# ── QWhizz integration ────────────────────────────────────────────────────────

def _send_to_qwhizz(cards: list[dict], deck_name: str) -> tuple[bool, str]:
    payload = {"deck_name": deck_name, "cards": cards, "source": "qwhizz_forge"}
    try:
        r = requests.post(
            f"{QWHIZZ_API_URL.rstrip('/')}/api/import",
            json=payload,
            timeout=15,
        )
        if r.status_code == 200:
            data = r.json()
            return True, f"Imported {data.get('imported', len(cards))} cards into '{deck_name}'"
        return False, f"QWhizz returned HTTP {r.status_code}: {r.text[:200]}"
    except requests.exceptions.ConnectionError:
        return False, f"Cannot connect to QWhizz forge importer at {QWHIZZ_API_URL}."
    except Exception as e:
        return False, str(e)


# ── URL fetching (with SSRF protection) ───────────────────────────────────────

def _fetch_url(url: str) -> str:
    valid, err = _validate_url(url)
    if not valid:
        st.error(f"URL not allowed: {err}")
        return ""
    try:
        from bs4 import BeautifulSoup
        r = requests.get(
            url,
            headers={"User-Agent": "QWhizzForge/1.0"},
            timeout=10,
            allow_redirects=True,
        )
        r.raise_for_status()

        # Validate Content-Type — only process text responses
        content_type = r.headers.get("Content-Type", "")
        if not any(t in content_type for t in ("text/html", "text/plain", "application/xhtml")):
            st.warning(f"Unsupported content type: {content_type}")
            return ""

        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        return soup.get_text(separator="\n", strip=True)[:_MAX_SOURCE_LEN]
    except Exception as e:
        st.warning(f"Could not fetch URL: {e}")
        return ""


# ── UI helpers ────────────────────────────────────────────────────────────────

def _bloom_badge(level: str) -> str:
    """Render a colored Bloom's level badge. Color comes from our own dict, not user input."""
    color = BLOOM_LEVELS.get(level, {}).get("color", "#6c757d")
    # level is validated against BLOOM_LEVELS keys before this is called
    safe_level = level if level in BLOOM_LEVELS else ""
    return (
        f'<span style="background:{color};color:white;padding:2px 8px;'
        f'border-radius:10px;font-size:0.75em;font-weight:600">'
        f'{safe_level}</span>'
    )


def _render_bloom_distribution(cards: list[dict]) -> None:
    counts = Counter(c.get("bloom_level", "?") for c in cards)
    cols   = st.columns(len(counts))
    for col, (level, count) in zip(cols, sorted(counts.items())):
        color = BLOOM_LEVELS.get(level, {}).get("color", "#6c757d")
        col.markdown(
            f'<div style="text-align:center;padding:8px;background:{color}22;'
            f'border-radius:8px;border:1px solid {color}">'
            f'<div style="color:{color};font-weight:700;font-size:1.3em">{count}</div>'
            f'<div style="color:{color};font-size:0.75em">{level}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )


def _render_card_previews(cards: list[dict]) -> None:
    for i, card in enumerate(cards):
        bloom = card.get("bloom_level", "")
        with st.expander(f"Card {i+1}: {card['question'][:80]}", expanded=(i == 0)):
            # Badge uses our own color dict — not user-supplied HTML
            st.markdown(
                f"{_bloom_badge(bloom)} &nbsp; "
                f"**{card.get('points', 1)} pt** &nbsp; "
                f"⏱ ~{card.get('estimated_time_seconds', 30)}s",
                unsafe_allow_html=True,
            )
            # Card content rendered with st.write (auto-escaped, not unsafe_allow_html)
            st.write(f"**Answer:** {card['answer']}")
            if card.get("wrong_answers"):
                st.write(f"**Distractors:** {', '.join(card['wrong_answers'])}")
            if card.get("hint"):
                st.write(f"**Hint:** {card['hint']}")
            if card.get("explanation"):
                st.write(f"**Explanation:** {card['explanation']}")
            if card.get("tags"):
                st.write(f"**Tags:** {', '.join(card['tags'])}")


# ── Public entry point ────────────────────────────────────────────────────────

def render_forge_tab(current_deck: str = "", username: str = "") -> None:
    """
    Render the QWhizz Forge tab. Call this from any QWhizz app's TabSpec.

    Args:
        current_deck: Pre-fill the deck name from the app's selected deck.
        username:     Current user (for future per-user forge history).
    """
    st.subheader("QWhizz Forge")
    st.caption("Generate Bloom's Taxonomy-aligned cards with Ollama and add them to any deck.")

    # ── Ollama availability check ─────────────────────────────────────────────
    if not _ollama_available():
        st.warning(
            f"Ollama is not reachable at `{OLLAMA_BASE}`. "
            "QWhizz Forge requires a local Ollama instance and cannot run on Streamlit Cloud. "
            "Run the app locally on your Mac Mini to use this feature."
        )
        return

    # ── Model selector + Bloom reference ─────────────────────────────────────
    col_model, col_ref = st.columns([1, 2])

    with col_model:
        models = _get_models()
        model  = st.selectbox(
            "Ollama Model",
            options=models,
            index=models.index(DEFAULT_MODEL) if DEFAULT_MODEL in models else 0,
            key="forge_model",
        )

    with col_ref:
        with st.expander("Bloom's Taxonomy Reference"):
            for name, info in BLOOM_LEVELS.items():
                if name == "Mixed":
                    continue
                st.markdown(
                    f'{_bloom_badge(name)} {info["description"]} — *{info["verbs"]}*',
                    unsafe_allow_html=True,
                )

    st.divider()

    # ── Generation options ────────────────────────────────────────────────────
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        topic_raw = st.text_input(
            "Topic",
            placeholder="e.g. DNA replication, Python decorators",
            max_chars=_MAX_TOPIC_LEN,
            key="forge_topic",
        )

        # Deck selector — pick existing or type a new name
        from data.deck_store import get_deck_names
        existing_decks = get_deck_names()
        NEW_DECK_OPTION = "➕ Create new deck..."
        deck_options = existing_decks + [NEW_DECK_OPTION]

        # Pre-select current_deck if it exists
        default_idx = existing_decks.index(current_deck) if current_deck in existing_decks else 0

        deck_choice = st.selectbox(
            "Add to Deck",
            options=deck_options,
            index=default_idx,
            key="forge_deck_select",
        )

        if deck_choice == NEW_DECK_OPTION:
            deck_raw = st.text_input(
                "New deck name",
                max_chars=_MAX_DECK_NAME_LEN,
                key="forge_deck_new",
                placeholder="Enter a name for the new deck",
            )
        else:
            deck_raw = deck_choice

    with col2:
        card_type  = st.selectbox("Card Type",  CARD_TYPES,        key="forge_card_type")
        difficulty = st.selectbox("Difficulty", DIFFICULTY_LEVELS, key="forge_difficulty", index=2)

    with col3:
        num_cards = st.slider("# of Cards", min_value=3, max_value=MAX_CARDS, value=10, key="forge_num_cards")

    # Sanitize free-text inputs
    topic     = _sanitize_topic(topic_raw)
    deck_name = _sanitize_deck_name(deck_raw) or _sanitize_topic(topic_raw)

    # Warn user if sanitization changed their input
    if topic != topic_raw.strip():
        st.caption(f"Topic sanitized to: *{topic}*")
    if deck_name != deck_raw.strip() and deck_raw.strip():
        st.caption(f"Deck name sanitized to: *{deck_name}*")

    # ── Bloom's level picker ──────────────────────────────────────────────────
    st.write("**Bloom's Level**")
    bloom_cols     = st.columns(len(BLOOM_LEVELS))
    selected_bloom = st.session_state.get("forge_bloom", "Mixed")

    for col, (level, info) in zip(bloom_cols, BLOOM_LEVELS.items()):
        color       = info["color"]
        is_selected = selected_bloom == level
        border      = f"3px solid {color}" if is_selected else "1px solid #dee2e6"
        bg          = f"{color}22"         if is_selected else "transparent"
        col.markdown(
            f'<div style="text-align:center;padding:8px 2px;background:{bg};'
            f'border-radius:8px;border:{border}">'
            f'<div style="font-size:1.2em">{info["icon"]}</div>'
            f'<div style="font-weight:600;color:{color};font-size:0.8em">{level}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        if col.button("·", key=f"forge_bloom_{level}", use_container_width=True, help=info["description"]):
            st.session_state["forge_bloom"] = level
            st.rerun()

    # Re-read after potential rerun; validate against known keys
    selected_bloom = st.session_state.get("forge_bloom", "Mixed")
    if selected_bloom not in BLOOM_LEVELS:
        selected_bloom = "Mixed"

    info = BLOOM_LEVELS[selected_bloom]
    if selected_bloom != "Mixed":
        st.caption(f"**{selected_bloom}:** {info['description']} — verbs: {info['verbs']}")
    else:
        st.caption("Cards will be distributed across all six Bloom's levels.")

    # ── Source material ───────────────────────────────────────────────────────
    source_text = ""

    with st.expander("Source Material (optional)"):
        src_paste, src_url, src_file = st.tabs(["Paste Text", "From URL", "Upload File"])

        with src_paste:
            raw_paste   = st.text_area(
                "Paste notes or reference material",
                height=150,
                max_chars=_MAX_SOURCE_LEN,
                key="forge_source_paste",
            )
            source_text = _sanitize_source(raw_paste)

        with src_url:
            url_input = st.text_input("URL", placeholder="https://...", key="forge_url")
            if st.button("Fetch", key="forge_fetch_url"):
                if url_input:
                    valid, err = _validate_url(url_input)
                    if not valid:
                        st.error(f"URL not allowed: {err}")
                    else:
                        with st.spinner("Fetching..."):
                            fetched = _fetch_url(url_input)
                        if fetched:
                            st.session_state["forge_fetched"] = fetched
                            st.success(f"Fetched {len(fetched)} characters")
            if "forge_fetched" in st.session_state:
                st.text_area(
                    "Fetched content",
                    st.session_state["forge_fetched"],
                    height=100,
                    key="forge_fetched_preview",
                )
                source_text = st.session_state["forge_fetched"]

        with src_file:
            uploaded = st.file_uploader(
                "PDF or text file",
                type=["pdf", "txt", "md"],
                key="forge_upload",
            )
            if uploaded:
                # Cap file size at 5MB
                raw_bytes = uploaded.read(5 * 1024 * 1024 + 1)
                if len(raw_bytes) > 5 * 1024 * 1024:
                    st.error("File too large. Maximum size is 5MB.")
                elif uploaded.type == "application/pdf":
                    try:
                        import io
                        import pdfplumber
                        with pdfplumber.open(io.BytesIO(raw_bytes)) as pdf:
                            source_text = "\n".join(p.extract_text() or "" for p in pdf.pages)
                        source_text = _sanitize_source(source_text)
                        st.success(f"Extracted {len(source_text)} characters")
                    except Exception as e:
                        st.error(f"PDF error: {e}")
                else:
                    source_text = _sanitize_source(raw_bytes.decode("utf-8", errors="ignore"))
                    st.success(f"Loaded {len(source_text)} characters")

    # ── Generate ──────────────────────────────────────────────────────────────
    st.divider()

    if st.button("Generate Cards", type="primary", disabled=not topic, key="forge_generate"):
        with st.spinner(f"Generating {num_cards} {selected_bloom}-level {card_type} cards with {model}..."):
            cards = _generate(
                model=model,
                topic=topic,
                source_text=source_text,
                card_type=card_type,
                difficulty=difficulty,
                bloom_level=selected_bloom,
                num_cards=num_cards,
            )
        if cards:
            st.session_state["forge_cards"]     = cards
            st.session_state["forge_deck_name"] = deck_name or topic
            st.success(f"Generated {len(cards)} cards")

    # ── Preview + send ────────────────────────────────────────────────────────
    if "forge_cards" in st.session_state:
        cards     = st.session_state["forge_cards"]
        deck_name = st.session_state.get("forge_deck_name", "")

        st.subheader(f"Preview — {len(cards)} cards")
        _render_bloom_distribution(cards)
        st.write("")
        _render_card_previews(cards)

        st.divider()

        col_dl, col_send = st.columns(2)

        with col_dl:
            safe_deck_name = re.sub(r"[^\w]", "_", deck_name)
            st.download_button(
                label="Download JSON",
                data=json.dumps(cards, indent=2),
                file_name=f"{safe_deck_name}_forge.json",
                mime="application/json",
                key="forge_download",
            )

        with col_send:
            send_raw  = st.text_input(
                "Deck name",
                value=deck_name,
                max_chars=_MAX_DECK_NAME_LEN,
                key="forge_send_deck",
            )
            send_deck = _sanitize_deck_name(send_raw)
            if st.button("Add to QWhizz", type="primary", key="forge_send"):
                if not send_deck:
                    st.error("Deck name cannot be empty.")
                else:
                    with st.spinner("Sending..."):
                        ok, msg = _send_to_qwhizz(cards, send_deck)
                    if ok:
                        st.success(msg)
                        st.session_state.pop("forge_cards", None)
                        st.rerun()
                    else:
                        st.error(msg)