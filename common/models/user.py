# models/user.py
from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class User(BaseModel):
    username: str                    # maps to MongoDB _id
    password: str
    real_name: str = ""
    email: str = ""
    is_admin: bool = False

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

    def to_mongo(self) -> dict:
        d = self.model_dump()
        d["_id"] = d.pop("username")
        return d

    @classmethod
    def from_mongo(cls, data: dict) -> "User":
        d = {**data, "username": data["_id"]}
        d.pop("_id", None)
        return cls.model_validate(d)