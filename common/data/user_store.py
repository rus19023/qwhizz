# data/user_store.py

from data.db import users, study_sessions
from datetime import datetime, timedelta


def get_all_usernames():
    """Get list of all registered usernames"""
    return sorted([user["_id"] for user in users.find({}, {"_id": 1})])


def create_user(username, password, is_admin=False):
    """Create a new user with password"""
    users.insert_one({
        "_id": username,
        "password": password,
        "is_admin": is_admin,
        "total_score": 0,
        "cards_studied": 0,
        "correct_answers": 0,
        "incorrect_answers": 0,
        "current_streak": 0,
        "best_streak": 0,
        "verification_passed": 0,
        "verification_failed": 0,
        "flagged": False,
        "created_at": datetime.utcnow()
    })


def get_user(username):
    """Get user data"""
    return users.find_one({"_id": username})


def update_user_score(username, points_delta, correct=True, verified=False):
    """Update user's score and stats"""
    increment = {
        "total_score": points_delta,
        "cards_studied": 1
    }

    if correct:
        increment["correct_answers"] = 1
        increment["current_streak"] = 1
    else:
        increment["incorrect_answers"] = 1

    if verified:
        if correct:
            increment["verification_passed"] = 1
        else:
            increment["verification_failed"] = 1

    users.update_one({"_id": username}, {"$inc": increment})

    # Update best streak if current is higher
    user = get_user(username)
    if correct and user["current_streak"] > user.get("best_streak", 0):
        users.update_one(
            {"_id": username},
            {"$set": {"best_streak": user["current_streak"]}}
        )

    # Reset streak if incorrect
    if not correct:
        users.update_one({"_id": username}, {"$set": {"current_streak": 0}})


def log_study_session(username, deck_name, card_question, response_time, correct, mode):
    """Log individual card responses for anti-cheat analysis"""
    study_sessions.insert_one({
        "username":      username,
        "deck_name":     deck_name,
        "card_question": card_question,
        "response_time": response_time,
        "correct":       correct,
        "mode":          mode,
        "timestamp":     datetime.utcnow()
    })


def get_deck_stats_for_user(username):
    """
    Return per-deck stats for a user aggregated from study_sessions.

    Returns a list of dicts:
      { deck_name, total, correct, incorrect, accuracy, last_studied }
    """
    pipeline = [
        {"$match": {"username": username}},
        {"$group": {
            "_id":          "$deck_name",
            "total":        {"$sum": 1},
            "correct":      {"$sum": {"$cond": ["$correct", 1, 0]}},
            "incorrect":    {"$sum": {"$cond": ["$correct", 0, 1]}},
            "last_studied": {"$max": "$timestamp"},
        }},
        {"$sort": {"_id": 1}},
    ]
    results = []
    for row in study_sessions.aggregate(pipeline):
        total = row["total"]
        results.append({
            "deck_name":    row["_id"],
            "total":        total,
            "correct":      row["correct"],
            "incorrect":    row["incorrect"],
            "accuracy":     round(row["correct"] / total * 100, 1) if total else 0.0,
            "last_studied": row["last_studied"],
        })
    return results


def get_suspicious_users():
    """Get users with suspicious patterns"""
    suspicious = []

    for user in users.find():
        username = user["_id"]

        total = user.get("cards_studied", 0)
        if total >= 100:
            accuracy = (user.get("correct_answers", 0) / total * 100) if total > 0 else 0
            if accuracy >= 99.5:
                suspicious.append({
                    "username": username,
                    "reason":   f"Suspiciously perfect accuracy: {accuracy:.1f}% over {total} cards",
                    "severity": "medium"
                })

        verif_total = user.get("verification_passed", 0) + user.get("verification_failed", 0)
        if verif_total >= 10:
            verif_accuracy = (user.get("verification_passed", 0) / verif_total * 100)
            if verif_accuracy < 50:
                suspicious.append({
                    "username": username,
                    "reason":   f"Low verification accuracy: {verif_accuracy:.1f}%",
                    "severity": "high"
                })

        recent_sessions = list(study_sessions.find({"username": username}).limit(50))
        if len(recent_sessions) >= 20:
            avg_time = sum(s.get("response_time", 0) for s in recent_sessions) / len(recent_sessions)
            if avg_time < 1:
                suspicious.append({
                    "username": username,
                    "reason":   f"Impossibly fast responses: {avg_time:.1f}s average",
                    "severity": "high"
                })

    return suspicious


def flag_user(username):
    users.update_one({"_id": username}, {"$set": {"flagged": True}})


def unflag_user(username):
    users.update_one({"_id": username}, {"$set": {"flagged": False}})


def reset_user_score(username):
    users.update_one({"_id": username}, {"$set": {
        "total_score": 0, "cards_studied": 0, "correct_answers": 0,
        "incorrect_answers": 0, "current_streak": 0,
        "verification_passed": 0, "verification_failed": 0,
    }})


def get_leaderboard(limit=10):
    return list(users.find({"flagged": {"$ne": True}}).sort("total_score", -1).limit(limit))