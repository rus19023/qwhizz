# core/chinese_deck_generator.py
"""
Chinese (Mandarin) deck generator for QWhizz.

Extends the existing ai_deck_generator.py provider pattern to produce
Chinese language flashcards using the flat Card field mapping:

    question  = Chinese character(s)          e.g. "你好"
    answer    = English meaning               e.g. "Hello / Hi"
    hint      = Pinyin with tone marks        e.g. "nǐ hǎo"
    tags      = content/level labels          e.g. ["chinese", "hsk1", "greeting"]
    image_url = Google Translate TTS URL      (audio — field repurposed)
    explanation = example sentence or note
    type      = "chinese_vocab" | "chinese_phrase" | "chinese_radical" | "chinese_tone"

Drop this file into your existing `core/` directory.
Call generate_chinese_deck() from your manage/import tab UI.
"""

from __future__ import annotations

import json
import re
import requests
import streamlit as st
from urllib.parse import quote

# ── Google Translate TTS URL builder ─────────────────────────────────────────

TTS_BASE = "https://translate.google.com/translate_tts"

def build_tts_url(chinese_text: str, lang: str = "zh-CN") -> str:
    """
    Build a Google Translate TTS URL for a Chinese word or phrase.
    Uses the informal 'tw-ob' client — no API key required.

    NOTE: This is an undocumented endpoint. Works as of 2025 but may break.
    Consider caching audio files locally for production use.
    """
    encoded = quote(chinese_text)
    return f"{TTS_BASE}?ie=UTF-8&q={encoded}&tl={lang}&client=tw-ob"


# ── System prompts per content type ──────────────────────────────────────────

_COMMON_SCHEMA = """
Return ONLY a valid JSON array. No markdown, no preamble, no trailing text.
Each element must be an object with EXACTLY these keys:
{
  "question":    "<Chinese character(s)>",
  "answer":      "<English meaning>",
  "hint":        "<Pinyin with tone marks>",
  "tags":        ["chinese", "<level or category>", ...],
  "explanation": "<example sentence in Chinese, then pinyin, then English translation>",
  "type":        "<see instructions>"
}
Rules:
- "question": Simplified Chinese characters only. No pinyin here.
- "hint": Proper tone marks (ā á ǎ à / ē é ě è / etc.), not numbers.
- "explanation": Always include a short usage example. Format:
    "Character sentence. Pīnyīn sentence. English translation."
- "tags": Always include "chinese". Add HSK level if known (hsk1–hsk6).
  Add a semantic tag (greeting, food, family, etc.).
- Do NOT include "image_url" — that is added programmatically.
"""

SYSTEM_PROMPTS = {
    "chinese_vocab": f"""You are a Mandarin Chinese language expert creating HSK flashcards.
Generate vocabulary flashcards for individual words or short compounds.
Set "type" to "chinese_vocab".
{_COMMON_SCHEMA}
""",

    "chinese_phrase": f"""You are a Mandarin Chinese language expert creating conversation flashcards.
Generate common phrases, sentences, or expressions used in real speech.
Set "type" to "chinese_phrase".
Each card should represent a full phrase (2–10 characters).
{_COMMON_SCHEMA}
""",

    "chinese_radical": f"""You are a Mandarin Chinese language expert creating character component flashcards.
Generate cards for Chinese radicals (部首) and common character components.
Set "type" to "chinese_radical".
For "answer": give the radical's meaning AND its positional name if it has one
  (e.g., "water / 氵on left side of characters").
For "explanation": list 2–3 example characters that contain this radical.
  Format: "水 (shuǐ), 河 (hé), 海 (hǎi) — all contain 氵meaning water."
{_COMMON_SCHEMA}
""",

    "chinese_tone": f"""You are a Mandarin Chinese language expert creating tone-practice flashcards.
Generate minimal pairs or tone-contrast cards that help learners distinguish tones.
Set "type" to "chinese_tone".
For "question": show two or more characters that share the same syllable but differ in tone.
  e.g. "mā 妈 / má 麻 / mǎ 马 / mà 骂"
For "answer": list meanings for each tone variant.
  e.g. "1st: mother | 2nd: hemp | 3rd: horse | 4th: scold"
For "hint": the shared base syllable without tone marks, e.g. "ma"
For "explanation": a mnemonic or tone-contour reminder.
  e.g. "妈麻马骂 — flat, rising, dip, falling. 'Mother scolds the horse eating hemp.'"
{_COMMON_SCHEMA}
""",
}

# ── Prompt builders ───────────────────────────────────────────────────────────

def _build_vocab_prompt(topic: str, hsk_level: int | None, num_cards: int) -> str:
    level_hint = f"Focus on HSK {hsk_level} vocabulary." if hsk_level else "Mix of beginner to intermediate vocabulary."
    return (
        f"Generate {num_cards} Mandarin vocabulary flashcards about: {topic}.\n"
        f"{level_hint}\n"
        f"Return ONLY the JSON array."
    )

def _build_phrase_prompt(topic: str, num_cards: int) -> str:
    return (
        f"Generate {num_cards} Mandarin conversation phrase flashcards about: {topic}.\n"
        f"Focus on phrases a learner would actually use in daily life.\n"
        f"Return ONLY the JSON array."
    )

def _build_radical_prompt(num_cards: int) -> str:
    return (
        f"Generate {num_cards} flashcards for the most common and useful Chinese radicals.\n"
        f"Prioritize radicals that appear in many high-frequency characters.\n"
        f"Return ONLY the JSON array."
    )

def _build_tone_prompt(syllables: list[str] | None, num_cards: int) -> str:
    if syllables:
        syl_list = ", ".join(syllables)
        return (
            f"Generate tone-practice flashcards for these syllables: {syl_list}.\n"
            f"Return ONLY the JSON array."
        )
    return (
        f"Generate {num_cards} tone-practice flashcards covering common syllables "
        f"where tone confusion is frequent (e.g. mā/mǎ, wèn/wén, shū/shú).\n"
        f"Return ONLY the JSON array."
    )


# ── Provider calls (reuses your existing pattern) ────────────────────────────

def _get_claude_headers() -> dict:
    """Fetch Anthropic API key from st.secrets."""
    try:
        api_key = st.secrets["ANTHROPIC_API_KEY"]
    except KeyError:
        api_key = st.secrets.get("anthropic", {}).get("api_key", "")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not found in secrets.toml")
    return {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }

def _call_claude(system: str, prompt: str, model: str = "claude-haiku-4-5-20251001") -> str:
    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers=_get_claude_headers(),
        json={
            "model": model,
            "max_tokens": 4000,
            "system": system,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=60,
    )
    response.raise_for_status()
    return response.json()["content"][0]["text"].strip()

def _call_openai(system: str, prompt: str, model: str = "gpt-4o-mini") -> str:
    try:
        api_key = st.secrets["OPENAI_API_KEY"]
    except KeyError:
        raise ValueError("OPENAI_API_KEY not found in secrets.toml")
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": 4000,
        },
        timeout=60,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"].strip()

def _call_ollama(system: str, prompt: str, model: str = "llama3.2") -> str:
    try:
        base_url = st.secrets.get("OLLAMA_BASE_URL", "http://localhost:11434")
    except Exception:
        base_url = "http://localhost:11434"
    response = requests.post(
        f"{base_url}/api/chat",
        json={
            "model": model,
            "stream": False,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
        },
        timeout=120,
    )
    response.raise_for_status()
    return response.json()["message"]["content"].strip()


# ── JSON parser ───────────────────────────────────────────────────────────────

def _parse_json_cards(raw: str) -> list[dict]:
    """Strip markdown fences and parse the JSON array."""
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
    # Find first '[' in case there's leading text
    start = raw.find("[")
    if start != -1:
        raw = raw[start:]
    cards = json.loads(raw)
    if not isinstance(cards, list):
        raise ValueError("Expected a JSON array")
    return cards


# ── TTS URL injection ─────────────────────────────────────────────────────────

def _inject_tts_urls(cards: list[dict]) -> list[dict]:
    """
    Add image_url = Google TTS URL for each card's question (Chinese characters).
    For tone cards, use just the shared syllable characters portion.
    """
    for card in cards:
        q = card.get("question", "")
        # For tone cards: extract just the characters (strip pinyin annotations)
        # e.g. "mā 妈 / má 麻" → try to find CJK characters
        cjk_only = re.sub(r"[^\u4e00-\u9fff\u3400-\u4dbf]", "", q)
        text_for_tts = cjk_only if cjk_only else q
        if text_for_tts:
            card["image_url"] = build_tts_url(text_for_tts)
    return cards


# ── Public API ────────────────────────────────────────────────────────────────

def generate_chinese_deck(
    content_type: str,
    provider: str = "claude",
    model: str | None = None,
    topic: str = "everyday life",
    hsk_level: int | None = None,
    num_cards: int = 20,
    syllables: list[str] | None = None,
) -> list[dict]:
    """
    Generate a Chinese flashcard deck.

    Args:
        content_type: One of "chinese_vocab", "chinese_phrase",
                      "chinese_radical", "chinese_tone"
        provider:     "claude" | "openai" | "ollama"
        model:        Override model name (None = use default)
        topic:        Theme/topic for vocab and phrase decks
        hsk_level:    1–6, used for vocab decks (None = mixed)
        num_cards:    Target number of cards
        syllables:    For tone decks — specific syllables to contrast

    Returns:
        List of card dicts ready for QWhizz import.
    """
    if content_type not in SYSTEM_PROMPTS:
        raise ValueError(
            f"Unknown content_type '{content_type}'. "
            f"Choose from: {list(SYSTEM_PROMPTS.keys())}"
        )

    system = SYSTEM_PROMPTS[content_type]

    if content_type == "chinese_vocab":
        prompt = _build_vocab_prompt(topic, hsk_level, num_cards)
    elif content_type == "chinese_phrase":
        prompt = _build_phrase_prompt(topic, num_cards)
    elif content_type == "chinese_radical":
        prompt = _build_radical_prompt(num_cards)
    else:  # chinese_tone
        prompt = _build_tone_prompt(syllables, num_cards)

    # Route to provider
    defaults = {"claude": "claude-haiku-4-5-20251001", "openai": "gpt-4o-mini", "ollama": "llama3.2"}
    model = model or defaults.get(provider, defaults["claude"])

    try:
        if provider == "claude":
            raw = _call_claude(system, prompt, model)
        elif provider == "openai":
            raw = _call_openai(system, prompt, model)
        elif provider == "ollama":
            raw = _call_ollama(system, prompt, model)
        else:
            st.error(f"Unknown provider: {provider}")
            return []

        cards = _parse_json_cards(raw)
        cards = _inject_tts_urls(cards)
        return cards

    except json.JSONDecodeError as e:
        st.error(f"AI returned invalid JSON: {e}")
    except Exception as e:
        st.error(f"Chinese deck generation failed ({provider}): {e}")

    return []
