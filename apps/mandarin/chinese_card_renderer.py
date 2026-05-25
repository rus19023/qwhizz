# common/ui/chinese_card_renderer.py
"""
Chinese flashcard renderer for QWhizz Streamlit app.

Renders a Card (using the flat Chinese field mapping) with:
  - Large character display with stroke-count-aware sizing
  - Pinyin with per-tone color coding
  - Audio playback button (Google TTS via image_url field)
  - Study-mode-aware field hiding
  - Tone reference legend

Study modes supported:
  "character"  → show character, hide pinyin + meaning
  "pinyin"     → show pinyin, hide character + meaning
  "meaning"    → show English meaning, hide character + pinyin
  "full"       → show everything (review/reveal mode)

Usage:
    from common.ui.chinese_card_renderer import render_chinese_card

    render_chinese_card(card_dict, study_mode="character")

card_dict keys used:
    question    → Chinese character(s)
    answer      → English meaning
    hint        → Pinyin with tone marks
    image_url   → Google TTS URL
    explanation → example sentence
    tags        → shown as chips
    type        → drives minor layout tweaks
"""

from __future__ import annotations
import re
import streamlit as st
import streamlit.components.v1 as components


# ── Tone color palette ────────────────────────────────────────────────────────
# Classic convention used in most Chinese textbooks:
TONE_COLORS = {
    1: "#e74c3c",   # 1st tone  — red    (flat/high)
    2: "#e67e22",   # 2nd tone  — orange (rising)
    3: "#27ae60",   # 3rd tone  — green  (dip-rise)
    4: "#2980b9",   # 4th tone  — blue   (falling)
    0: "#7f8c8d",   # neutral   — gray
}

# Vowels with tone marks mapped to tone number
_TONE_VOWELS = {
    "ā": 1, "á": 2, "ǎ": 3, "à": 4,
    "ē": 1, "é": 2, "ě": 3, "è": 4,
    "ī": 1, "í": 2, "ǐ": 3, "ì": 4,
    "ō": 1, "ó": 2, "ǒ": 3, "ò": 4,
    "ū": 1, "ú": 2, "ǔ": 3, "ù": 4,
    "ǖ": 1, "ǘ": 2, "ǚ": 3, "ǜ": 4,
}


def _detect_tone(syllable: str) -> int:
    """Return the tone number (1-4) for a pinyin syllable, or 0 for neutral."""
    for char, tone in _TONE_VOWELS.items():
        if char in syllable:
            return tone
    return 0


def _colorize_pinyin(pinyin: str) -> str:
    """
    Return an HTML string with each pinyin syllable colored by tone.
    Splits on spaces/slashes, colors each token, rejoins.
    """
    # Split on whitespace, slashes, or em-dashes but keep delimiters
    tokens = re.split(r"(\s+|/|–|—|,)", pinyin)
    parts = []
    for token in tokens:
        tone = _detect_tone(token)
        color = TONE_COLORS.get(tone, TONE_COLORS[0])
        if any(c in token for c in _TONE_VOWELS):
            parts.append(f'<span style="color:{color};font-weight:600">{token}</span>')
        else:
            parts.append(token)
    return "".join(parts)


# ── Character sizing ──────────────────────────────────────────────────────────

def _char_font_size(text: str) -> str:
    """Scale font size based on character count."""
    n = len(text.replace(" ", "").replace("/", ""))
    if n <= 1:
        return "5rem"
    if n <= 2:
        return "4rem"
    if n <= 4:
        return "3rem"
    if n <= 8:
        return "2.2rem"
    return "1.6rem"


# ── Tone legend ───────────────────────────────────────────────────────────────

def render_tone_legend():
    """Render a compact tone color/contour legend."""
    labels = [
        (1, "ā", "flat"),
        (2, "á", "rising"),
        (3, "ǎ", "dip-rise"),
        (4, "à", "falling"),
        (0, "a", "neutral"),
    ]
    cols = st.columns(5)
    for col, (tone, mark, name) in zip(cols, labels):
        color = TONE_COLORS[tone]
        col.markdown(
            f'<div style="text-align:center">'
            f'<span style="font-size:1.6rem;color:{color};font-weight:700">{mark}</span><br>'
            f'<span style="font-size:0.7rem;color:#888">{name}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )


# ── Audio button ──────────────────────────────────────────────────────────────

def render_audio_button(tts_url: str, label: str = "🔊 Listen"):
    """
    Render an HTML audio element with a play button.
    Uses the Google TTS URL stored in card['image_url'].

    NOTE: Google TTS is an undocumented endpoint.
    Works in most browsers when the URL is opened directly.
    We embed it as an <audio> tag with autoplay disabled.
    """
    # Encode the URL safely for embedding
    safe_url = tts_url.replace('"', "%22")
    audio_html = f"""
    <audio id="zh-audio" src="{safe_url}" preload="none"></audio>
    <button
        onclick="document.getElementById('zh-audio').play()"
        style="
            background: #2980b9;
            color: white;
            border: none;
            border-radius: 8px;
            padding: 8px 18px;
            font-size: 1rem;
            cursor: pointer;
            margin: 6px 0;
        "
    >{label}</button>
    """
    components.html(audio_html, height=55)


# ── Tag chips ─────────────────────────────────────────────────────────────────

def _render_tags(tags: list[str]):
    if not tags:
        return
    chip_html = " ".join(
        f'<span style="'
        f'background:#f0f4f8;border-radius:12px;padding:2px 10px;'
        f'font-size:0.75rem;color:#555;margin:2px;display:inline-block">'
        f'{tag}</span>'
        for tag in tags
        if tag != "chinese"  # skip the universal tag
    )
    st.markdown(chip_html, unsafe_allow_html=True)


# ── Type badge ────────────────────────────────────────────────────────────────

_TYPE_LABELS = {
    "chinese_vocab":   ("📖", "Vocabulary"),
    "chinese_phrase":  ("💬", "Phrase"),
    "chinese_radical": ("⬡", "Radical"),
    "chinese_tone":    ("🎵", "Tone Practice"),
}

def _render_type_badge(card_type: str):
    icon, label = _TYPE_LABELS.get(card_type, ("🃏", card_type))
    st.caption(f"{icon} {label}")


# ── Main render function ──────────────────────────────────────────────────────

def render_chinese_card(
    card: dict,
    study_mode: str = "full",
    show_audio: bool = True,
    show_tags: bool = True,
    show_explanation: bool = True,
):
    """
    Render a Chinese flashcard in the QWhizz study UI.

    Args:
        card:             Card dict (flat mapping: question=char, answer=meaning,
                          hint=pinyin, image_url=TTS URL)
        study_mode:       "character" | "pinyin" | "meaning" | "full"
        show_audio:       Whether to show the TTS audio button
        show_tags:        Whether to show content tags
        show_explanation: Whether to show the example sentence
    """
    character = card.get("question", "")
    meaning   = card.get("answer", "")
    pinyin    = card.get("hint", "")
    tts_url   = card.get("image_url", "")
    explanation = card.get("explanation", "")
    tags      = card.get("tags", [])
    card_type = card.get("type", "chinese_vocab")

    show_char    = study_mode in ("full", "pinyin", "meaning")  # hide only in "character" self-test
    show_pinyin  = study_mode in ("full", "character", "meaning")
    show_meaning = study_mode in ("full", "character", "pinyin")

    # For self-test modes we reveal on the flip side — handled by caller.
    # Here we render whatever is visible for this mode.

    _render_type_badge(card_type)
    st.markdown("---")

    # ── Character ────────────────────────────────────────────────────────────
    if show_char and character:
        font_size = _char_font_size(character)
        st.markdown(
            f'<div style="'
            f'text-align:center;'
            f'font-size:{font_size};'
            f'font-family:"Noto Sans SC","PingFang SC","Microsoft YaHei",sans-serif;'
            f'line-height:1.2;'
            f'margin:12px 0;'
            f'letter-spacing:0.05em;'
            f'">{character}</div>',
            unsafe_allow_html=True,
        )
    elif not show_char:
        st.markdown(
            '<div style="text-align:center;font-size:3rem;color:#ccc;margin:12px 0">？</div>',
            unsafe_allow_html=True,
        )

    # ── Audio ────────────────────────────────────────────────────────────────
    if show_audio and tts_url:
        col_l, col_c, col_r = st.columns([1, 1, 1])
        with col_c:
            render_audio_button(tts_url)

    # ── Pinyin ───────────────────────────────────────────────────────────────
    if show_pinyin and pinyin:
        colored = _colorize_pinyin(pinyin)
        st.markdown(
            f'<div style="text-align:center;font-size:1.3rem;margin:6px 0">'
            f'{colored}</div>',
            unsafe_allow_html=True,
        )
    elif not show_pinyin:
        st.markdown(
            '<div style="text-align:center;font-size:1.3rem;color:#ccc;margin:6px 0">'
            '· · · · ·</div>',
            unsafe_allow_html=True,
        )

    # ── Meaning ──────────────────────────────────────────────────────────────
    if show_meaning and meaning:
        st.markdown(
            f'<div style="text-align:center;font-size:1.1rem;color:#444;margin:8px 0">'
            f'{meaning}</div>',
            unsafe_allow_html=True,
        )
    elif not show_meaning:
        st.markdown(
            '<div style="text-align:center;font-size:1.1rem;color:#ccc;margin:8px 0">'
            '——</div>',
            unsafe_allow_html=True,
        )

    # ── Explanation (example sentence) ───────────────────────────────────────
    if show_explanation and explanation and study_mode == "full":
        st.markdown("---")
        st.markdown("**Example:**")
        st.markdown(
            f'<div style="font-size:0.9rem;color:#555;line-height:1.7">'
            f'{explanation}</div>',
            unsafe_allow_html=True,
        )

    # ── Tags ─────────────────────────────────────────────────────────────────
    if show_tags and tags:
        st.markdown("")
        _render_tags(tags)


# ── Study mode selector ───────────────────────────────────────────────────────

def render_chinese_study_mode_selector(key: str = "zh_study_mode") -> str:
    """
    Render a study-mode radio and return the selected mode string.
    Drop this above your card render loop.
    """
    mode_labels = {
        "character": "👁 Character → guess pinyin + meaning",
        "pinyin":    "🔤 Pinyin → guess character + meaning",
        "meaning":   "🌐 English → guess character + pinyin",
        "full":      "✅ Full review (show all)",
    }
    choice = st.radio(
        "Study mode",
        options=list(mode_labels.keys()),
        format_func=lambda k: mode_labels[k],
        horizontal=True,
        key=key,
    )
    return choice


# ── Standalone deck previewer (for manage tab) ────────────────────────────────

def render_chinese_deck_preview(cards: list[dict], max_preview: int = 5):
    """
    Render a compact table preview of Chinese cards — useful in the manage/import tab.
    Shows character, pinyin, meaning, type, and audio link.
    """
    if not cards:
        st.info("No cards to preview.")
        return

    st.markdown(f"**{len(cards)} card(s) — preview:**")

    preview = cards[:max_preview]
    for i, card in enumerate(preview, 1):
        char    = card.get("question", "")
        py      = card.get("hint", "")
        meaning = card.get("answer", "")
        ctype   = card.get("type", "")
        tts     = card.get("image_url", "")

        colored_py = _colorize_pinyin(py) if py else ""

        with st.expander(f"{i}. {char}  {py}  —  {meaning[:40]}"):
            col1, col2 = st.columns([2, 3])
            with col1:
                fs = _char_font_size(char)
                st.markdown(
                    f'<div style="font-size:{fs};font-family:\'Noto Sans SC\',sans-serif">'
                    f'{char}</div>',
                    unsafe_allow_html=True,
                )
                if tts:
                    render_audio_button(tts, label="🔊")
            with col2:
                st.markdown(
                    f'<div style="font-size:1.1rem">{colored_py}</div>',
                    unsafe_allow_html=True,
                )
                st.write(meaning)
                _render_tags(card.get("tags", []))
                st.caption(ctype)

    if len(cards) > max_preview:
        st.caption(f"… and {len(cards) - max_preview} more cards.")
