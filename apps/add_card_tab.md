# Enhanced Flashcard System - Feature Guide

## New Features

### 1. Multiple Choice (up to 10 options)
Cards can now have up to 10 multiple choice options with a single correct answer.

### 2. Multi-Select Questions
Questions that require selecting multiple correct answers (checkboxes).

### 3. Image Support
Display images (charts, diagrams, tables) with questions.

### 4. True/False Questions
Simple true/false questions with automatic checking.

---

## Card Format Examples

### Standard Flashcard
```python
{
    "question": "What is DNA?",
    "answer": "Deoxyribonucleic acid",
    "type": "flashcard"
}
```

### Multiple Choice (4 options)
```python
{
    "question": "What are the four DNA bases?",
    "answer": "A, T, G, C (Adenine, Thymine, Guanine, Cytosine)",
    "type": "multiple_choice",
    "options": [
        "A, T, G, C",      # Index 0 - CORRECT
        "A, U, G, C",      # Index 1
        "A, T, X, Y",      # Index 2
        "B, D, E, F"       # Index 3
    ],
    "correct_index": 0
}
```

### Multiple Choice (10 options)
```python
{
    "question": "Which organelle is responsible for ATP production?",
    "answer": "Mitochondria",
    "type": "multiple_choice",
    "options": [
        "Nucleus",
        "Ribosome",
        "Mitochondria",    # Index 2 - CORRECT
        "Golgi apparatus",
        "Endoplasmic reticulum",
        "Lysosome",
        "Chloroplast",
        "Vacuole",
        "Peroxisome",
        "Centrosome"
    ],
    "correct_index": 2
}
```

### Multi-Select (Multiple correct answers)
```python
{
    "question": "Which of the following are purines?",
    "answer": "Adenine and Guanine are purines (double-ring structures)",
    "type": "multi_select",
    "options": [
        "Adenine",     # Index 0 - CORRECT
        "Thymine",     # Index 1
        "Guanine",     # Index 2 - CORRECT
        "Cytosine",    # Index 3
        "Uracil",      # Index 4
        "Ribose"       # Index 5
    ],
    "correct_indices": [0, 2],  # Must select BOTH
    "num_correct": 2            # Fixed number expected
}
```

### True/False
```python
{
    "question": "DNA is double-stranded",
    "answer": "True - DNA forms a double helix structure with two complementary strands",
    "type": "true_false",
    "correct_answer": True
}
```

### Card with Image
```python
{
    "question": "What process is shown in this diagram?",
    "answer": "DNA Replication - the process of copying DNA before cell division",
    "type": "multiple_choice",
    "image_url": "https://example.com/dna_replication.png",
    "options": [
        "DNA Replication",
        "Transcription",
        "Translation",
        "DNA Repair"
    ],
    "correct_index": 0
}
```

---

## Adding Cards via UI

The admin "Add Card" tab now supports:

1. **Card Type Selector**: Choose flashcard, multiple_choice, multi_select, or true_false
2. **Image URL Field**: Optional image URL for diagrams/charts
3. **Options Builder**: Dynamic form for adding 2-10 options
4. **Correct Answer Selector**: 
   - Single select for multiple choice
   - Multi-select for multi-select questions
   - True/False toggle for true/false questions

---

## Study Modes

### Flashcard Mode (📇)
- Traditional flip cards
- Works with all card types
- Honor system

### Multiple Choice Mode (🎯)
- Shows only multiple_choice type cards
- Auto-generates options from other cards if not specified
- Single correct answer

### Multi-Select Mode (☑️)
- Shows only multi_select type cards
- Requires selecting ALL correct answers
- Checkboxes interface

### True/False Mode (✓✗)
- Shows only true_false type cards
- Simple binary choice
- Fast review

### Quiz Mode (✍️)
- Type your answer
- Fuzzy matching (80% similarity threshold)
- Works with all card types

### Commit Mode (🎯)
- Commit before revealing
- 3-second minimum delay
- Anti-cheat verification

### Hardcore Mode (🔥)
- All features enabled
- 5-second delay
- Type + commit required

---

## Database Schema

Cards are stored in MongoDB with this structure:

```javascript
{
    "_id": "Biology",  // Deck name
    "cards": [
        {
            "question": "What is mitosis?",
            "answer": "Cell division producing two identical daughter cells",
            "type": "flashcard"  // or "multiple_choice", "multi_select", "true_false"
            // Optional fields:
            "image_url": "https://...",
            "options": ["opt1", "opt2", ...],
            "correct_index": 0,
            "correct_indices": [0, 2],
            "num_correct": 2,
            "correct_answer": true
        }
    ]
}
```

---

## Points System

**Base Points:**
- ✓ Correct: +10 points
- ✗ Wrong: -3 points

**Streak Bonus:**
- +5 points per card in streak
- Example: 5-card streak = 10 + (5 × 5) = 35 points!

**All Game Modes:** Full points (no penalty for difficulty)

---

## Implementation Checklist

To enable these features in your app:

1. ✅ Update `core/study_modes.py` with new modes
2. ✅ Update `ui/components.py` with new UI components
3. ✅ Create `data/card_format.py` for validation
4. ✅ Create `core/game_mode_logic.py` for game logic
5. ✅ Update `ui/study_tab.py` to route modes correctly
6. ✅ Update `ui/add_card_tab.py` to support new fields
7. ⬜ Update `data/deck_store.py` if needed
8. ⬜ Migrate existing cards (optional)

---

## Image Hosting Options

For image URLs, you can use:

1. **Direct URLs**: Link to images hosted anywhere
2. **Imgur**: Free image hosting
3. **GitHub**: Upload to repository and use raw.githubusercontent.com URLs
4. **Cloud Storage**: AWS S3, Google Cloud Storage, etc.
5. **Local Files**: Place in `/static` folder and use relative paths

Example local path:
```python
"image_url": "/static/images/dna_structure.png"
```

---

## Tips for Creating Good Questions

### Multiple Choice:
- Make distractors plausible but clearly wrong
- Avoid "all of the above" or "none of the above"
- Keep options similar in length

### Multi-Select:
- Clearly state how many to select: "Select ALL that apply"
- Use 4-8 options with 2-4 correct answers
- Make sure incorrect options are clearly wrong

### True/False:
- Avoid absolute words like "always" and "never"
- Make questions clear and unambiguous
- Provide detailed explanations in the answer field

### Images:
- Use high-quality, clear diagrams
- Label important parts
- Ensure images load quickly
- Include alt text in answer for accessibility
