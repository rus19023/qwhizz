# ═══════════════════════════════════════════════════════════════════════════════
# QWhizz Chinese Integration — README
# ═══════════════════════════════════════════════════════════════════════════════
#
# Files delivered:
#
#   core/chinese_deck_generator.py      AI deck generation for Chinese content
#   data/chinese_decks/hsk1_vocab.json  20 HSK1 vocabulary cards (ready to import)
#   data/chinese_decks/radicals_common.json  15 common radical cards
#   data/chinese_decks/tone_practice.json    10 tone contrast/sandhi cards
#   data/chinese_decks/common_phrases.json   12 practical phrase cards
#   common/ui/chinese_card_renderer.py  Streamlit card display component
#
# ── Step 1: Drop files into your project ───────────────────────────────────────
#
#   Copy each file to the matching path in your QWhizz project directory.
#   No new dependencies needed — uses only streamlit, requests, re, json.
#
# ── Step 2: Import the JSON decks ──────────────────────────────────────────────
#
#   Use your existing QWhizz JSON import UI.
#   Each JSON file is a valid array of Card-compatible dicts.
#   Suggested deck names:
#     hsk1_vocab.json      → "Chinese HSK1 Vocabulary"
#     radicals_common.json → "Chinese Radicals — Common"
#     tone_practice.json   → "Chinese Tone Practice"
#     common_phrases.json  → "Chinese Phrases — Daily Life"
#
# ── Step 3: Wire the renderer into your study_tab.py ──────────────────────────
#
#   In common/ui/study_tab.py, detect Chinese card types and delegate:
#
#   from common.ui.chinese_card_renderer import (
#       render_chinese_card,
#       render_chinese_study_mode_selector,
#   )
#
#   CHINESE_TYPES = {"chinese_vocab", "chinese_phrase", "chinese_radical", "chinese_tone"}
#
#   def render_card(card: dict, ...):
#       if card.get("type") in CHINESE_TYPES:
#           study_mode = render_chinese_study_mode_selector()
#           render_chinese_card(card, study_mode=study_mode)
#       else:
#           # existing render logic
#           ...
#
# ── Step 4: Add Chinese generation to your manage tab ─────────────────────────
#
#   In your manage/import tab (manage_tab.py), add a "Generate Chinese Deck" section:
#
#   from core.chinese_deck_generator import generate_chinese_deck
#   from common.ui.chinese_card_renderer import render_chinese_deck_preview
#
#   with st.expander("🀄 Generate Chinese Deck"):
#       content_type = st.selectbox(
#           "Content type",
#           ["chinese_vocab", "chinese_phrase", "chinese_radical", "chinese_tone"],
#           format_func=lambda x: {
#               "chinese_vocab":   "Vocabulary (HSK)",
#               "chinese_phrase":  "Phrases / Sentences",
#               "chinese_radical": "Radicals & Components",
#               "chinese_tone":    "Tone Practice Cards",
#           }[x],
#       )
#
#       topic = ""
#       hsk_level = None
#       syllables = None
#
#       if content_type in ("chinese_vocab", "chinese_phrase"):
#           topic = st.text_input("Topic / theme", value="everyday life")
#       if content_type == "chinese_vocab":
#           hsk_level = st.selectbox("HSK level (optional)", [None, 1, 2, 3, 4, 5, 6])
#       if content_type == "chinese_tone":
#           raw = st.text_input("Specific syllables (comma-separated, optional)", "")
#           syllables = [s.strip() for s in raw.split(",") if s.strip()] or None
#
#       num_cards = st.slider("Number of cards", 5, 40, 20)
#
#       # Reuse your existing provider selector here:
#       # provider_label = st.selectbox("AI Provider", list(PROVIDERS.keys()))
#       # provider = PROVIDERS[provider_label]
#
#       if st.button("✨ Generate Chinese Cards"):
#           with st.spinner("Generating..."):
#               cards = generate_chinese_deck(
#                   content_type=content_type,
#                   provider=provider,           # from your existing selector
#                   topic=topic,
#                   hsk_level=hsk_level,
#                   num_cards=num_cards,
#                   syllables=syllables,
#               )
#           if cards:
#               st.success(f"Generated {len(cards)} cards!")
#               render_chinese_deck_preview(cards)
#               # Then let the user name the deck and import:
#               deck_name = st.text_input("Save as deck name")
#               if st.button("💾 Import to QWhizz") and deck_name:
#                   # call your existing deck import logic here
#                   pass
#
# ── Step 5: Add to ai_deck_generator.py SYSTEM_PROMPT (optional) ──────────────
#
#   If you want your GENERIC generator to also handle Chinese when the source
#   material is in Chinese, add this to the bottom of your existing SYSTEM_PROMPT:
#
SYSTEM_PROMPT_CHINESE_ADDENDUM = """
If the source material contains Chinese characters or is about the Chinese language:
- Set "question" to the Chinese character(s) — simplified characters only
- Set "answer" to the English meaning
- Set "hint" to pinyin with proper tone marks (ā á ǎ à, NOT a1 a2 a3 a4)
- Set "type" to one of: "chinese_vocab", "chinese_phrase", "chinese_radical", "chinese_tone"
- Set "explanation" to a short example sentence in format:
    "Chinese sentence. Pīnyīn sentence. English translation."
- Set "tags" to include "chinese" and the HSK level if determinable (e.g. "hsk1")
- Leave "image_url" empty — it will be populated programmatically
"""
#
# ── Notes on Google TTS URLs ───────────────────────────────────────────────────
#
#   Format:
#     https://translate.google.com/translate_tts?ie=UTF-8&q=<encoded>&tl=zh-CN&client=tw-ob
#
#   - Works without an API key (undocumented endpoint)
#   - Some browsers/environments block it due to CORS or rate limiting
#   - For production: consider caching the audio files locally on first play
#   - For Streamlit Cloud: audio plays via the embedded HTML component;
#     the <audio> tag approach in chinese_card_renderer.py handles CORS correctly
#   - Language codes: zh-CN (Mandarin simplified), zh-TW (Traditional/Taiwanese)
#
# ── Noto Sans SC font ──────────────────────────────────────────────────────────
#
#   For best character rendering, add to your theme CSS or index.html:
#
#   @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;700&display=swap');
#
#   The renderer specifies it in the font-family stack with OS fallbacks,
#   so characters will render even without this — but Noto SC looks best.
#
# ═══════════════════════════════════════════════════════════════════════════════
