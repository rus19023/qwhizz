# ui/ai_generate_tab.py
"""
AI-powered deck generation tab.

Supports:
  - Multiple file uploads (.pdf, .docx, .txt) — concatenated before generation
  - Web URL extraction
  - Raw text paste
  - Provider / model selection
  - Duplicate detection against the existing deck
  - Per-card approve/skip before saving
"""

from __future__ import annotations
import streamlit as st

from core.ai_deck_generator import (
    generate_from_file,
    generate_from_url,
    generate_from_text,
    PROVIDERS,
    DEFAULT_MODELS,
)
from data.deck_store import get_deck_names, get_deck, create_deck
from models.card import Card


# ── Duplicate detection ───────────────────────────────────────────────────────

def _is_duplicate(question: str, existing_questions: list[str], threshold: float = 0.85) -> bool:
    """
    Check if a question is a near-duplicate of any existing question.
    Uses simple normalised character overlap (no embeddings needed).

    Args:
        question (str): Candidate question text.
        existing_questions (list[str]): Lowercased existing questions.
        threshold (float): Similarity threshold (0-1). 0.85 works well in practice.

    Returns:
        bool: True if a near-duplicate exists.
    """
    from difflib import SequenceMatcher
    q = question.lower().strip()
    for existing in existing_questions:
        ratio = SequenceMatcher(None, q, existing).ratio()
        if ratio >= threshold:
            return True
    return False


# ── Model lists ──────────────────────────────────────────────────────────────

# Hardcoded lists for cloud providers — update as new models are released
CLAUDE_MODELS = [
    "claude-opus-4-5",
    "claude-sonnet-4-5",
    "claude-haiku-4-5-20251001",
    "claude-opus-4-20250514",
    "claude-sonnet-4-20250514",
]

OPENAI_MODELS = [
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-4-turbo",
    "gpt-3.5-turbo",
]

PROVIDER_MODELS: dict[str, list[str]] = {
    "claude": CLAUDE_MODELS,
    "openai": OPENAI_MODELS,
    "ollama": [],  # populated live from Ollama API
}


def _get_ollama_models() -> list[str]:
    """
    Fetch the list of locally available Ollama models from the Ollama API.

    Returns:
        list[str]: Model name strings (e.g. ["llama3.2:latest", "phi3:mini"]),
                   or empty list if Ollama is unreachable.
    """
    import requests
    from core.ai_deck_generator import _get_secret
    base_url = _get_secret("OLLAMA_BASE_URL") or "http://localhost:11434"
    try:
        response = requests.get(f"{base_url}/api/tags", timeout=5)
        response.raise_for_status()
        return [m["name"] for m in response.json().get("models", [])]
    except Exception:
        return []


def _get_models_for_provider(provider: str) -> list[str]:
    """
    Return the model list for a given provider.
    For Ollama, fetches live from the local API.
    For others, returns the hardcoded list.

    Args:
        provider (str): Provider key — "claude", "openai", or "ollama".

    Returns:
        list[str]: Available model names, or empty list on failure.
    """
    if provider == "ollama":
        return _get_ollama_models()
    return PROVIDER_MODELS.get(provider, [])



# ── Cost / token estimator ────────────────────────────────────────────────────

# Pricing per 1M tokens (input / output) in USD — update as pricing changes
# Sources: anthropic.com/pricing, openai.com/pricing
PRICING: dict[str, dict[str, float]] = {
    "claude-opus-4-5":           {"input": 15.00, "output": 75.00},
    "claude-sonnet-4-5":         {"input":  3.00, "output": 15.00},
    "claude-haiku-4-5-20251001": {"input":  0.80, "output":  4.00},
    "claude-opus-4-20250514":    {"input": 15.00, "output": 75.00},
    "claude-sonnet-4-20250514":  {"input":  3.00, "output": 15.00},
    "gpt-4o":                    {"input":  2.50, "output": 10.00},
    "gpt-4o-mini":               {"input":  0.15, "output":  0.60},
    "gpt-4-turbo":               {"input": 10.00, "output": 30.00},
    "gpt-3.5-turbo":             {"input":  0.50, "output":  1.50},
}

# Approximate generation speed (tokens/sec) per provider type
SPEED_ESTIMATE: dict[str, int] = {
    "claude": 80,
    "openai": 60,
    "ollama": 10,   # CPU-bound local model
}


def _estimate_cost(
    text: str,
    num_cards: int,
    provider: str,
    model: str | None,
) -> dict:
    """
    Estimate token usage, generation time, and cost before running.

    Args:
        text (str): The source text (already truncated to max_chars if needed).
        num_cards (int): Number of cards requested.
        provider (str): Provider key.
        model (str | None): Model name.

    Returns:
        dict: {input_tokens, output_tokens, total_tokens, cost_usd,
               speed_tps, est_seconds, model, provider}
    """
    # Rough token estimate: ~4 chars per token for English text
    input_tokens  = len(text) // 4
    # Output estimate: ~120 tokens per card (question + answer + JSON overhead)
    output_tokens = num_cards * 120

    price = PRICING.get(model or "", None)
    if price:
        cost = (input_tokens / 1_000_000 * price["input"]
                + output_tokens / 1_000_000 * price["output"])
    else:
        cost = None  # Ollama or unknown model — free / unknown

    speed    = SPEED_ESTIMATE.get(provider, 20)
    est_secs = output_tokens / speed

    return {
        "input_tokens":  input_tokens,
        "output_tokens": output_tokens,
        "total_tokens":  input_tokens + output_tokens,
        "cost_usd":      cost,
        "speed_tps":     speed,
        "est_seconds":   est_secs,
        "model":         model,
        "provider":      provider,
    }


def _render_cost_estimate(
    text: str,
    num_cards: int,
    provider: str,
    model: str | None,
) -> None:
    """
    Render a cost/speed estimate panel before the generate button.

    Args:
        text (str): Source text (used to estimate input tokens).
        num_cards (int): Requested card count.
        provider (str): Provider key.
        model (str | None): Model name.
    """
    # Apply same truncation as generate_cards_from_text
    max_chars = 4000 if provider == "ollama" else 12000
    truncated = text[:max_chars] if len(text) > max_chars else text
    was_truncated = len(text) > max_chars

    est = _estimate_cost(truncated, num_cards, provider, model)

    with st.expander("📊 Estimated usage & cost", expanded=True):
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Input tokens",  f"~{est['input_tokens']:,}")
            st.metric("Output tokens", f"~{est['output_tokens']:,}")

        with col2:
            st.metric("Total tokens",  f"~{est['total_tokens']:,}")
            if est["cost_usd"] is not None:
                st.metric("Est. cost",
                          f"~${est['cost_usd']:.4f}" if est["cost_usd"] < 0.01
                          else f"~${est['cost_usd']:.3f}")
            else:
                st.metric("Est. cost", "Free (local)")

        with col3:
            st.metric("Speed",        f"~{est['speed_tps']} tok/s")
            secs = est["est_seconds"]
            if secs < 60:
                time_str = f"~{secs:.0f}s"
            else:
                time_str = f"~{secs/60:.1f} min"
            st.metric("Est. time", time_str)

        if was_truncated:
            st.caption(
                f"⚠️ Source text truncated from {len(text):,} to {max_chars:,} chars "
                f"for {provider}. Token estimates reflect truncated input."
            )
        if est["cost_usd"] is not None:
            st.caption(
                "💡 Cost estimates are approximate based on published token prices. "
                "Actual cost may vary slightly."
            )
        elif provider == "ollama":
            st.caption("💡 Ollama runs locally — no API cost. Speed estimate assumes CPU inference.")

# ── Main renderer ─────────────────────────────────────────────────────────────

def render_ai_generate_tab() -> None:
    """Render the AI deck generation tab."""
    st.subheader("🤖 Generate Cards with AI")

    # ── Deck selection ────────────────────────────────────────────────────────
    deck_option = st.radio(
        "Target deck:",
        ["Add to existing deck", "Create new deck"],
        horizontal=True,
        key="aigen_deck_option",
    )

    existing_decks = get_deck_names()
    deck_name = ""

    if deck_option == "Add to existing deck":
        if existing_decks:
            deck_name = st.selectbox(
                "Select deck:",
                options=existing_decks,
                key="aigen_deck_select",
            )
        else:
            st.warning("No decks yet — switch to 'Create new deck'.")
    else:
        new_name = st.text_input("New deck name:", key="aigen_new_deck_name")
        deck_name = new_name.strip()

    if not deck_name:
        st.info("Choose or name a deck above to continue.")
        return

    # ── Provider / model ──────────────────────────────────────────────────────
    st.write("**AI Provider:**")
    col_prov, col_model = st.columns([2, 3])
    with col_prov:
        provider_label = st.selectbox(
            "Provider",
            options=list(PROVIDERS.keys()),
            key="aigen_provider",
            label_visibility="collapsed",
        )
        provider = PROVIDERS[provider_label]

    with col_model:
        available_models = _get_models_for_provider(provider)
        if available_models:
            default = DEFAULT_MODELS.get(provider, available_models[0])
            default_idx = available_models.index(default) if default in available_models else 0
            model = st.selectbox(
                "Model",
                options=available_models,
                index=default_idx,
                key=f"aigen_model_{provider}",
                label_visibility="collapsed",
            )
        else:
            # Ollama unreachable or unknown provider — fall back to text input
            model_input = st.text_input(
                "Model (not reachable — type manually)",
                value=DEFAULT_MODELS.get(provider, ""),
                key=f"aigen_model_{provider}_manual",
            )
            model = model_input.strip() or None

    # ── Number of cards ───────────────────────────────────────────────────────
    num_cards = st.slider(
        "Approximate number of cards to generate",
        min_value=5,
        max_value=50,
        value=15,
        step=5,
        key="aigen_num_cards",
    )

    # ── Source selection ──────────────────────────────────────────────────────
    st.write("**Source:**")
    source_type = st.radio(
        "Source type",
        ["📄 Files", "🌐 URL", "📝 Paste text"],
        horizontal=True,
        key="aigen_source_type",
        label_visibility="collapsed",
    )

    source_ready = False
    source_label = ""

    if source_type == "📄 Files":
        st.info(
            "Upload one or more files. Text will be concatenated before generation.\n\n"
            "Supported: **.pdf · .docx · .txt**"
        )
        uploaded_files = st.file_uploader(
            "Choose files",
            type=["pdf", "docx", "txt"],
            accept_multiple_files=True,
            key="aigen_files",
        )
        if uploaded_files:
            st.caption(f"{len(uploaded_files)} file(s) selected: " +
                       ", ".join(f.name for f in uploaded_files))
            source_ready = True
            source_label = ", ".join(f.name for f in uploaded_files)

    elif source_type == "🌐 URL":
        url_input = st.text_input(
            "Web page URL",
            placeholder="https://example.com/article",
            key="aigen_url",
        )
        if url_input.strip():
            source_ready = True
            source_label = url_input.strip()

    else:  # Paste text
        pasted = st.text_area(
            "Paste study material here",
            height=200,
            key="aigen_paste",
        )
        if pasted.strip():
            source_ready = True
            source_label = "pasted text"

    # ── Generate button ───────────────────────────────────────────────────────
    if not source_ready:
        st.info("Add a source above to continue.")
        return

    # Build a text sample for estimation
    # For files: estimate from total file sizes (4 bytes ≈ 1 token)
    # For URL/paste: use actual text length
    if source_type == "📄 Files":
        est_text = "x" * sum(getattr(f, "size", 0) for f in uploaded_files)
    elif source_type == "🌐 URL":
        est_text = "x" * max(len(url_input) * 50, 2000)  # rough page size guess
    else:
        est_text = pasted

    _render_cost_estimate(est_text, num_cards, provider, model)

    if provider == "ollama":
        st.caption("💡 For local models, 5–8 cards is recommended to avoid timeouts.")

    if st.button("🚀 Generate Cards", type="primary", key="aigen_run_btn"):
        with st.spinner(f"Generating ~{num_cards} cards from {source_label}..."):
            try:
                if source_type == "📄 Files":
                    _, raw_cards = generate_from_file(
                        uploaded_files, num_cards, provider, model
                    )
                elif source_type == "🌐 URL":
                    _, raw_cards = generate_from_url(
                        url_input.strip(), num_cards, provider, model
                    )
                else:
                    _, raw_cards = generate_from_text(
                        pasted.strip(), num_cards, provider, model
                    )
            except Exception as e:
                st.error(f"Generation failed: {e}")
                return

        if not raw_cards:
            st.error("No cards were generated. Check your source content and API key.")
            return

        # ── Deduplicate against existing deck ─────────────────────────────────
        existing_cards  = get_deck(deck_name)
        existing_qs     = [c.get("question", "").lower().strip() for c in existing_cards]
        
        unique    = []
        dupes     = []
        batch_qs  = []  # track duplicates within the new batch itself

        for card in raw_cards:
            q = (card.get("question") or "").strip()
            if not q:
                continue
            if _is_duplicate(q, existing_qs + batch_qs):
                dupes.append(card)
            else:
                unique.append(card)
                batch_qs.append(q.lower())

        st.success(
            f"Generated **{len(raw_cards)}** cards · "
            f"**{len(unique)}** unique · "
            f"**{len(dupes)}** duplicate(s) removed"
        )

        if dupes:
            with st.expander(f"🔁 {len(dupes)} duplicate(s) skipped"):
                for d in dupes:
                    st.caption(f"• {d.get('question', '')[:80]}")

        if not unique:
            st.warning("All generated cards were duplicates of existing ones.")
            return

        st.session_state["aigen_proposals"] = unique
        st.session_state["aigen_deck_name"] = deck_name

    # ── Preview & approve ─────────────────────────────────────────────────────
    proposals = st.session_state.get("aigen_proposals", [])
    target    = st.session_state.get("aigen_deck_name", deck_name)

    if not proposals:
        return

    st.write(f"### 📋 Review {len(proposals)} Card(s) for '{target}'")
    st.caption("Uncheck any card you want to skip before saving.")

    approved_indices = []
    for i, card in enumerate(proposals):
        q = card.get("question", "")
        a = card.get("answer", "")
        with st.expander(f"Card {i+1}: {q[:60]}..."):
            approved = st.checkbox("✅ Include this card", value=True, key=f"aigen_approve_{i}")
            if approved:
                approved_indices.append(i)
            st.markdown(f"**Q:** {q}")
            st.markdown(f"**A:** {a}")
            card_type = card.get("type", "flashcard")
            if card_type != "flashcard":
                st.caption(f"Type: {card_type}")
            if card.get("options"):
                st.caption("Options: " + " · ".join(card["options"]))

    st.write(f"**{len(approved_indices)}** card(s) selected.")

    col_save, col_discard = st.columns(2)
    with col_save:
        if st.button(
            "💾 Save to Deck", type="primary",
            disabled=not approved_indices,
            key="aigen_save_btn",
        ):
            approved_cards = [proposals[i] for i in approved_indices]

            # Create deck if new
            if target not in get_deck_names():
                create_deck(target)

            from data.db import get_database
            db = get_database()
            db.decks.update_one(
                {"_id": target},
                {"$push": {"cards": {"$each": approved_cards}}},
                upsert=True,
            )

            st.success(f"✅ Saved {len(approved_cards)} card(s) to '{target}'!")
            st.balloons()
            del st.session_state["aigen_proposals"]
            del st.session_state["aigen_deck_name"]
            st.rerun()

    with col_discard:
        if st.button("🗑️ Discard All", key="aigen_discard_btn"):
            del st.session_state["aigen_proposals"]
            del st.session_state["aigen_deck_name"]
            st.rerun()