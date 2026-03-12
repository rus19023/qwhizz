# models.py

from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# ── Card sub-models ───────────────────────────────────────────────────────────

class FeedbackLink(BaseModel):
    label: str = ""
    url: str


class CardFeedback(BaseModel):
    text: str = ""
    images: list[str] = Field(default_factory=list)
    links: list[FeedbackLink] = Field(default_factory=list)


class Card(BaseModel):
    question: str
    answer: str
    wrong_answers: list[str] = Field(default_factory=list)
    hint: str = ""
    tags: list[str] = Field(default_factory=list)
    image_url: str = ""
    feedback: CardFeedback = Field(default_factory=CardFeedback)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def to_mongo(self) -> dict:
        """Serialize to a MongoDB-ready dict (excludes empty optional fields)."""
        d = self.model_dump()
        # Drop empty optionals to keep documents tidy
        for key in ("hint", "image_url"):
            if not d[key]:
                d.pop(key)
        if not any([d["feedback"]["text"], d["feedback"]["images"], d["feedback"]["links"]]):
            d.pop("feedback")
        if not d["tags"]:
            d.pop("tags")
        if not d["wrong_answers"]:
            d.pop("wrong_answers")
        return d

    @classmethod
    def from_mongo(cls, data: dict) -> "Card":
        """Build a Card from a raw MongoDB document."""
        # Normalise legacy wrong-answer field names
        if "distractors" in data and "wrong_answers" not in data:
            data = {**data, "wrong_answers": data.pop("distractors")}
        if "incorrect_answers" in data and "wrong_answers" not in data:
            data = {**data, "wrong_answers": data.pop("incorrect_answers")}
        return cls.model_validate(data)

    @classmethod
    def from_import_row(cls, row: dict) -> "Card":
        """
        Build a Card from a flat import row (CSV / JSON bulk import).
        Accepts both old and new field names.
        """
        wrong = (
            row.get("wrong_answers")
            or row.get("distractors")
            or row.get("incorrect_answers")
            or []
        )
        # If it came in as a pipe-separated string (CSV), split it
        if isinstance(wrong, str):
            wrong = [w.strip() for w in wrong.split("|") if w.strip()]

        feedback_links_raw = row.get("feedback_links", [])
        if isinstance(feedback_links_raw, str):
            # CSV: "Label1|url1,Label2|url2"
            parsed_links = []
            for pair in feedback_links_raw.split(","):
                parts = pair.split("|", 1)
                if len(parts) == 2:
                    parsed_links.append(FeedbackLink(label=parts[0].strip(), url=parts[1].strip()))
                elif len(parts) == 1 and parts[0].strip():
                    parsed_links.append(FeedbackLink(url=parts[0].strip()))
            feedback_links_raw = parsed_links

        feedback_images_raw = row.get("feedback_images", [])
        if isinstance(feedback_images_raw, str):
            feedback_images_raw = [u.strip() for u in feedback_images_raw.split("|") if u.strip()]

        return cls(
            question=row.get("question", ""),
            answer=row.get("answer", ""),
            wrong_answers=wrong,
            hint=row.get("hint", ""),
            tags=[t.strip() for t in row.get("tags", "").split(",") if t.strip()]
                 if isinstance(row.get("tags"), str) else row.get("tags", []),
            image_url=row.get("image_url", ""),
            feedback=CardFeedback(
                text=row.get("feedback_text", row.get("feedback", {}).get("text", "")),
                images=feedback_images_raw,
                links=feedback_links_raw,
            ),
        )

    def to_export_row(self) -> dict:
        """Flat dict suitable for CSV export."""
        return {
            "question":        self.question,
            "answer":          self.answer,
            "wrong_answers":   " | ".join(self.wrong_answers),
            "hint":            self.hint,
            "tags":            ", ".join(self.tags),
            "image_url":       self.image_url,
            "feedback_text":   self.feedback.text,
            "feedback_images": " | ".join(self.feedback.images),
            "feedback_links":  ", ".join(
                f"{lnk.label}|{lnk.url}" for lnk in self.feedback.links
            ),
        }


# ── User model ────────────────────────────────────────────────────────────────

class User(BaseModel):
    username: str                           # maps to MongoDB _id
    password: str
    real_name: str = ""
    email: str = ""
    is_admin: bool = False

    # Stats
    total_score: int = 0
    cards_studied: int = 0
    correct_answers: int = 0
    incorrect_answers: int = 0
    current_streak: int = 0
    best_streak: int = 0
    verification_passed: int = 0
    verification_failed: int = 0
    flagged: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def to_mongo(self) -> dict:
        d = self.model_dump()
        d["_id"] = d.pop("username")
        return d

    @classmethod
    def from_mongo(cls, data: dict) -> "User":
        d = {**data, "username": data["_id"]}
        d.pop("_id", None)
        return cls.model_validate(d)
    
    