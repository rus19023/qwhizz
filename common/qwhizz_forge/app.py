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
from datetime import datetime, timezone

import requests
import streamlit as st

# ── Config (read from whichever app's secrets.toml is loaded) ─────────────────
def _cfg(key: str, default: str) -> str:
    return st.secrets.get("qwhizz_forge", {}).get(key, default)

OLLAMA_BASE    = _cfg("ollama_url",   "http://localhost:11434")
QWHIZZ_API_URL = _cfg("qwhizz_url",  "http://localhost:8502")
DEFAULT_MODEL  = _cfg("default_model", "llama3")
MAX_CARDS      = 30

CARD_TYPES        = ["flashcard", "multiple_choice", "true_false"]
DIFFICULTY_LEVELS = ["easy", "medium", "hard", "mixed"]

# ── Bloom's Taxonomy ──────────────────────────────────────────────────────────
BLOOM_LEVELS: dict[str, dict] = {
    "Remember":   {"description": "Recall facts and basic concepts",          "verbs": "define, list, recall, recognize, repeat, state",         "icon": "1️⃣", "color": "#6c757d", "points": 1},
    "Understand": {"description": "Explain ideas in your own words",          "verbs": "classify, describe, explain, summarize, interpret",       "icon": "2️⃣", "color": "#0d6efd", "points": 2},
    "Apply":      {"description": "Use information in new situations",        "verbs": "calculate, demonstrate, solve, use, implement",           "icon": "3️⃣", "color": "#198754", "points": 3},
    "Analyze":    {"description": "Draw connections and break down info",     "verbs": "compare, contrast, differentiate, examine, break down",   "icon": "4️⃣", "color": "#fd7e14", "points": 4},
    "Evaluate":   {"description": "Justify a decision or course of action",   "verbs": "argue, defend, judge, critique, assess, justify",         "icon": "5️⃣", "color": "#dc3545", "points": 5},
    "Create":     {"description": "Produce new or original work",             "verbs": "design, construct, develop, formulate, compose, plan",    "icon": "6️⃣", "color": "#6f42c1", "points": 5},
    "Mixed":      {"description": "Distribute across all Bloom's levels",     "verbs": "all levels",                                             "icon": "🔀", "color": "#20c997", "points": 3},
}


# ── Ollama helpers ────────────────────────────────────────────────────────────

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

    source = f"\n\nSource material:\n{source_text[:4000]}" if source_text.strip() else ""

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
    bloom = raw.get("bloom_level", "Remember")
    if bloom not in BLOOM_LEVELS or bloom == "Mixed":
        bloom = "Remember"
    return {
        "question":               str(raw.get("question", "")).strip(),
        "answer":                 str(raw.get("answer", "")).strip(),
        "wrong_answers":          [str(w) for w in raw.get("wrong_answers", [])],
        "hint":                   str(raw.get("hint", "") or ""),
        "tags":                   [str(t) for t in raw.get("tags", [])],
        "explanation":            str(raw.get("explanation", "") or ""),
        "feedback":               {"text": "", "images": [], "links": []},
        "type":                   raw.get("type", "flashcard"),
        "bloom_level":            bloom,
        "estimated_time_seconds": int(raw.get("estimated_time_seconds", 30)),
        "points":                 int(raw.get("points", BLOOM_LEVELS[bloom]["points"])),
    }


# ── QWhizz integration ────────────────────────────────────────────────────────

def _send_to_qwhizz(cards: list[dict], deck_name: str) -> tuple[bool, str]:
    payload = {"deck_name": deck_name, "cards": cards, "source": "qwhizz_forge"}
    try:
        r = requests.post(f"{QWHIZZ_API_URL.rstrip('/')}/api/import", json=payload, timeout=15)
        if r.status_code == 200:
            data = r.json()
            return True, f"Imported {data.get('imported', len(cards))} cards into '{deck_name}'"
        return False, f"QWhizz returned HTTP {r.status_code}: {r.text[:200]}"
    except requests.exceptions.ConnectionError:
        return False, f"Cannot connect to QWhizz forge importer at {QWHIZZ_API_URL}."
    except Exception as e:
        return False, str(e)


# ── Source material helpers ───────────────────────────────────────────────────

def _fetch_url(url: str) -> str:
    try:
        from bs4 import BeautifulSoup
        r = requests.get(url, headers={"User-Agent": "QWhizzForge/1.0"}, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        return soup.get_text(separator="\n", strip=True)
    except Exception as e:
        st.warning(f"Could not fetch URL: {e}")
        return ""


# ── UI helpers ────────────────────────────────────────────────────────────────

def _bloom_badge(level: str) -> str:
    color = BLOOM_LEVELS.get(level, {}).get("color", "#6c757d")
    return (
        f'<span style="background:{color};color:white;padding:2px 8px;'
        f'border-radius:10px;font-size:0.75em;font-weight:600">{level}</span>'
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
            st.markdown(
                f"{_bloom_badge(bloom)} &nbsp; "
                f"**{card.get('points', 1)} pt** &nbsp; "
                f"⏱ ~{card.get('estimated_time_seconds', 30)}s",
                unsafe_allow_html=True,
            )
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

    # ── Model selector + Bloom reference (in columns to save space) ───────────
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
        topic     = st.text_input("Topic", placeholder="e.g. DNA replication, Python decorators", key="forge_topic")
        deck_name = st.text_input("Add to Deck", value=current_deck or topic, key="forge_deck")

    with col2:
        card_type  = st.selectbox("Card Type",  CARD_TYPES,        key="forge_card_type")
        difficulty = st.selectbox("Difficulty", DIFFICULTY_LEVELS, key="forge_difficulty", index=2)

    with col3:
        num_cards = st.slider("# of Cards", min_value=3, max_value=MAX_CARDS, value=10, key="forge_num_cards")

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

    selected_bloom = st.session_state.get("forge_bloom", "Mixed")
    info = BLOOM_LEVELS[selected_bloom]
    if selected_bloom != "Mixed":
        st.caption(f"**{selected_bloom}:** {info['description']} — verbs: {info['verbs']}")
    else:
        st.caption("Cards will be distributed across all six Bloom's levels.")

    # ── Source material ───────────────────────────────────────────────────────
    with st.expander("Source Material (optional)"):
        src_paste, src_url, src_file = st.tabs(["Paste Text", "From URL", "Upload File"])
        source_text = ""

        with src_paste:
            source_text = st.text_area("Paste notes or reference material", height=150, key="forge_source_paste")

        with src_url:
            url_input = st.text_input("URL", placeholder="https://...", key="forge_url")
            if st.button("Fetch", key="forge_fetch_url"):
                if url_input:
                    with st.spinner("Fetching..."):
                        fetched = _fetch_url(url_input)
                    if fetched:
                        st.session_state["forge_fetched"] = fetched
                        st.success(f"Fetched {len(fetched)} characters")
            if "forge_fetched" in st.session_state:
                st.text_area("Fetched content", st.session_state["forge_fetched"], height=100, key="forge_fetched_preview")
                source_text = st.session_state["forge_fetched"]

        with src_file:
            uploaded = st.file_uploader("PDF or text file", type=["pdf", "txt", "md"], key="forge_upload")
            if uploaded:
                if uploaded.type == "application/pdf":
                    try:
                        import pdfplumber
                        with pdfplumber.open(uploaded) as pdf:
                            source_text = "\n".join(p.extract_text() or "" for p in pdf.pages)
                        st.success(f"Extracted {len(source_text)} characters")
                    except Exception as e:
                        st.error(f"PDF error: {e}")
                else:
                    source_text = uploaded.read().decode("utf-8", errors="ignore")
                    st.success(f"Loaded {len(source_text)} characters")

    # ── Generate button ───────────────────────────────────────────────────────
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
            st.download_button(
                label="Download JSON",
                data=json.dumps(cards, indent=2),
                file_name=f"{deck_name.replace(' ', '_')}_forge.json",
                mime="application/json",
                key="forge_download",
            )

        with col_send:
            send_deck = st.text_input("Deck name", value=deck_name, key="forge_send_deck")
            if st.button("Add to QWhizz", type="primary", key="forge_send"):
                with st.spinner("Sending..."):
                    ok, msg = _send_to_qwhizz(cards, send_deck)
                if ok:
                    st.success(msg)
                    st.session_state.pop("forge_cards", None)
                    st.rerun()
                else:
                    st.error(msg)