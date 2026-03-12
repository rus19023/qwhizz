# models/card.py
from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field


class CardLink(BaseModel):
    label: str = ""
    url: str

    def to_dict(self) -> dict:
        return {"label": self.label, "url": self.url}

    @classmethod
    def from_dict(cls, d: dict) -> "CardLink":
        return cls(label=d.get("label", ""), url=d.get("url", ""))


class CardFeedback(BaseModel):
    text: Optional[str] = None
    images: list[str] = Field(default_factory=list)
    links: list[CardLink] = Field(default_factory=list)

    def is_empty(self) -> bool:
        return not self.text and not self.images and not self.links

    def to_dict(self) -> dict:
        d: dict = {}
        if self.text:
            d["text"] = self.text
        if self.images:
            d["images"] = self.images
        if self.links:
            d["links"] = [lnk.to_dict() for lnk in self.links]
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "CardFeedback":
        if not d:
            return cls()
        links = [CardLink.from_dict(lnk) if isinstance(lnk, dict) else lnk
                 for lnk in d.get("links", [])]
        return cls(
            text=d.get("text") or None,
            images=d.get("images", []),
            links=links,
        )


class Card(BaseModel):
    question: str
    answer: str
    wrong_answers: list[str] = Field(default_factory=list)
    hint: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    image_url: Optional[str] = None
    explanation: Optional[str] = None          # shown after answering (rich text)
    feedback: CardFeedback = Field(default_factory=CardFeedback)

    # Game-mode fields (optional — only present on MC / multi-select / T/F cards)
    type: str = "flashcard"
    options: list[str] = Field(default_factory=list)
    correct_index: Optional[int] = None        # multiple_choice
    correct_indices: list[int] = Field(default_factory=list)  # multi_select
    num_correct: Optional[int] = None          # multi_select
    correct_answer: Optional[bool] = None      # true_false

    # ── Serialisation ─────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        """Produce a clean MongoDB-ready dict, omitting empty/None fields."""
        d: dict = {
            "question": self.question,
            "answer": self.answer,
        }
        if self.wrong_answers:
            d["wrong_answers"] = self.wrong_answers
        if self.hint:
            d["hint"] = self.hint
        if self.tags:
            d["tags"] = self.tags
        if self.image_url:
            d["image_url"] = self.image_url
        if self.explanation:
            d["explanation"] = self.explanation
        if not self.feedback.is_empty():
            d["feedback"] = self.feedback.to_dict()

        # Game-mode fields
        if self.type != "flashcard":
            d["type"] = self.type
        if self.options:
            d["options"] = self.options
        if self.correct_index is not None:
            d["correct_index"] = self.correct_index
        if self.correct_indices:
            d["correct_indices"] = self.correct_indices
        if self.num_correct is not None:
            d["num_correct"] = self.num_correct
        if self.correct_answer is not None:
            d["correct_answer"] = self.correct_answer

        return d

    @classmethod
    def from_dict(cls, d: dict) -> "Card":
        """Build a Card from a raw MongoDB document or import row."""
        data = dict(d)
        data.pop("index", None)   # strip the helper key added by get_all_cards_with_indices

        # Normalise legacy wrong-answer field names
        for legacy in ("distractors", "incorrect_answers"):
            if legacy in data and "wrong_answers" not in data:
                data["wrong_answers"] = data.pop(legacy)

        # Deserialise nested feedback
        raw_fb = data.pop("feedback", {})
        feedback = CardFeedback.from_dict(raw_fb if isinstance(raw_fb, dict) else {})

        return cls(feedback=feedback, **data)

    # ── Flat CSV export row ────────────────────────────────────────────────────

    def to_export_row(self) -> dict:
        return {
            "question":        self.question,
            "answer":          self.answer,
            "wrong_answers":   " | ".join(self.wrong_answers),
            "hint":            self.hint or "",
            "tags":            ", ".join(self.tags),
            "image_url":       self.image_url or "",
            "explanation":     self.explanation or "",
            "feedback_text":   self.feedback.text or "",
            "feedback_images": " | ".join(self.feedback.images),
            "feedback_links":  ", ".join(
                f"{lnk.label}|{lnk.url}" for lnk in self.feedback.links
            ),
        }

    @classmethod
    def from_import_row(cls, row: dict) -> "Card":
        """Build a Card from a flat CSV/JSON import row."""
        wrong = row.get("wrong_answers") or row.get("distractors") or row.get("incorrect_answers") or []
        if isinstance(wrong, str):
            wrong = [w.strip() for w in wrong.split("|") if w.strip()]

        tags = row.get("tags", [])
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(",") if t.strip()]

        # Feedback
        fb_links_raw = row.get("feedback_links", "")
        fb_links = []
        if isinstance(fb_links_raw, str):
            for pair in fb_links_raw.split(","):
                parts = pair.split("|", 1)
                if len(parts) == 2:
                    fb_links.append(CardLink(label=parts[0].strip(), url=parts[1].strip()))
                elif len(parts) == 1 and parts[0].strip():
                    fb_links.append(CardLink(url=parts[0].strip()))

        fb_images_raw = row.get("feedback_images", "")
        fb_images = [u.strip() for u in fb_images_raw.split("|") if u.strip()] \
            if isinstance(fb_images_raw, str) else fb_images_raw

        feedback = CardFeedback(
            text=row.get("feedback_text") or None,
            images=fb_images,
            links=fb_links,
        )

        return cls(
            question=row.get("question", ""),
            answer=row.get("answer", ""),
            wrong_answers=wrong,
            hint=row.get("hint") or None,
            tags=tags,
            image_url=row.get("image_url") or None,
            explanation=row.get("explanation") or None,
            feedback=feedback,
        )