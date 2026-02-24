# data/decks.py

from data.db import decks

DECK_NAME = "No One Sits Alone"

FLASHCARDS = [
    {"type": "flashcard", "question": "What is the main message of 'No One Sits Alone'?",
     "answer": "Living the gospel includes making room for all in Christ’s restored Church."},

    {"type": "flashcard", "question": "What object does Elder Gong use to introduce the idea of studying culture?",
     "answer": "Fortune cookies."},

    {"type": "flashcard", "question": "What did Elder Gong learn about the origin of fortune cookies?",
     "answer": "They are not originally part of Chinese culture."},

    {"type": "flashcard", "question": "What method does Elder Gong describe for comparing practices across settings?",
     "answer": "Cultural triangulation."},

    {"type": "flashcard", "question": "About how many international migrants are reported in the talk?",
     "answer": "281 million international migrants."},

    {"type": "flashcard", "question": "How many languages are mentioned as spoken in Church congregations?",
     "answer": "125 languages."},

    {"type": "flashcard", "question": "Which scripture allegory is referenced about gathering and grafting people together?",
     "answer": "Jacob 5 and the allegory of the olive tree."},

    {"type": "flashcard", "question": "What phrase summarizes the welcoming spirit Elder Gong teaches for church?",
     "answer": "Room in the inn / no one sits alone."},

    {"type": "flashcard", "question": "What does Mosiah 18:21 invite us to do?",
     "answer": "Knit our hearts together in love."},

    {"type": "flashcard", "question": "What question did a young man ask Elder Gong?",
     "answer": "Can I still go to heaven?"},
]

TRUE_FALSE_CARDS = [
    # TRUE statements
    {"type": "true_false",
     "question": "Fortune cookies are not originally part of Chinese culture.",
     "answer": "True. Elder Gong explains they are not originally part of Chinese culture.",
     "correct_answer": True},

    {"type": "true_false",
     "question": "Elder Gong teaches that living the gospel includes making room for all in Christ’s restored Church.",
     "answer": "True. This is the central theme of the talk.",
     "correct_answer": True},

    {"type": "true_false",
     "question": "Elder Gong says 'no one sits alone' includes emotional and spiritual belonging, not just physical seating.",
     "answer": "True. He explicitly expands the meaning beyond where someone sits.",
     "correct_answer": True},

    {"type": "true_false",
     "question": "Elder Gong references Mosiah 18:21 as an invitation to knit our hearts together in love.",
     "answer": "True. He uses this scripture to encourage unity and love.",
     "correct_answer": True},

    # FALSE statements (crafted to be clearly incorrect)
    {"type": "true_false",
     "question": "Fortune cookies originated as a traditional food in Beijing restaurants.",
     "answer": "False. Elder Gong notes fortune cookies are not originally part of Chinese culture and are not typically found in Beijing restaurants.",
     "correct_answer": False},

    {"type": "true_false",
     "question": "Elder Gong teaches that the best approach is to tolerate others, not genuinely welcome them.",
     "answer": "False. He urges us not merely to accommodate or tolerate but to genuinely welcome, acknowledge, minister, and love.",
     "correct_answer": False},

    {"type": "true_false",
     "question": "Elder Gong says social media and artificial intelligence always eliminate loneliness.",
     "answer": "False. He says they can leave people yearning for human closeness and touch.",
     "correct_answer": False},

    {"type": "true_false",
     "question": "Elder Gong teaches that Church positions are a ladder where we move upward over others.",
     "answer": "False. He teaches we move forward, not upward or downward, in Church positions.",
     "correct_answer": False},
]

ESSAY_CARDS = [
    {"type": "essay",
     "question": "Explain what Elder Gong means by “no one sits alone,” including physical, emotional, and spiritual inclusion.",
     "answer": "Rubric: greet/sit with those alone; extend belonging emotionally/spiritually; connect through Christ, covenants, ordinances; genuine welcome/ministering/love."},

    {"type": "essay",
     "question": "How do fortune cookies illustrate the difference between cultural practices and gospel culture?",
     "answer": "Rubric: practices vary by location; comparing settings reveals what is culture vs gospel; triangulation helps distinguish traditions from gospel values."},

    {"type": "essay",
     "question": "How do the parables of the great supper/wedding feast teach inclusion in the Lord’s Church?",
     "answer": "Rubric: invited guests refuse; servants gather widely; include overlooked people; 'all nations invited'; Church as 'inn' with room for all."},

    {"type": "essay",
     "question": "What is gospel culture (per the talk) and what kinds of traditions should we give up?",
     "answer": "Rubric: unique gospel values/practices; give up anything contrary to commandments; examples: chastity, church attendance, honesty/integrity, Word of Wisdom items."},
]

CARDS = FLASHCARDS + TRUE_FALSE_CARDS + ESSAY_CARDS

decks.update_one(
    {"_id": DECK_NAME},
    {"$set": {"cards": CARDS}},
    upsert=True
)

print(f"Imported '{DECK_NAME}' with {len(CARDS)} cards.")
