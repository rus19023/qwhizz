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
        
    users.update_one(
        {"_id": username},
        {
            "$inc": increment
        }
    )
    
    # Update best streak if current is higher
    user = get_user(username)
    if correct and user["current_streak"] > user.get("best_streak", 0):
        users.update_one(
            {"_id": username},
            {"$set": {"best_streak": user["current_streak"]}}
        )
    
    # Reset streak if incorrect
    if not correct:
        users.update_one(
            {"_id": username},
            {"$set": {"current_streak": 0}}
        )


def log_study_session(username, deck_name, card_question, response_time, correct, mode):
    """Log individual card responses for anti-cheat analysis"""
    study_sessions.insert_one({
        "username": username,
        "deck_name": deck_name,
        "card_question": card_question,
        "response_time": response_time,
        "correct": correct,
        "mode": mode,
        "timestamp": datetime.utcnow()
    })


def get_suspicious_users():
    """Get users with suspicious patterns"""
    suspicious = []
    
    for user in users.find():
        username = user["_id"]
        
        # Check 1: ONLY flag if 100% accuracy (literally perfect) with many cards
        total = user.get("cards_studied", 0)
        if total >= 100:  # Increased threshold
            accuracy = (user.get("correct_answers", 0) / total * 100) if total > 0 else 0
            if accuracy >= 99.5:  # Changed to 99.5% (almost perfect)
                suspicious.append({
                    "username": username,
                    "reason": f"Suspiciously perfect accuracy: {accuracy:.1f}% over {total} cards",
                    "severity": "medium"
                })
        
        # Check 2: Failed verification checks (this is the real cheater detector)
        verif_total = user.get("verification_passed", 0) + user.get("verification_failed", 0)
        if verif_total >= 10:
            verif_accuracy = (user.get("verification_passed", 0) / verif_total * 100)
            if verif_accuracy < 50:  # Failing verifications = likely cheating
                suspicious.append({
                    "username": username,
                    "reason": f"Low verification accuracy: {verif_accuracy:.1f}% (likely clicking 'Got it' without knowing)",
                    "severity": "high"
                })
        
        # Check 3: Impossible speed (average < 1 second = likely auto-clicking)
        recent_sessions = list(study_sessions.find({"username": username}).limit(50))
        if len(recent_sessions) >= 20:
            avg_time = sum(s.get("response_time", 0) for s in recent_sessions) / len(recent_sessions)
            if avg_time < 1:  # Changed to 1 second
                suspicious.append({
                    "username": username,
                    "reason": f"Impossibly fast responses: {avg_time:.1f}s average",
                    "severity": "high"
                })
    
    return suspicious


def flag_user(username):
    """Flag a user as suspicious"""
    users.update_one(
        {"_id": username},
        {"$set": {"flagged": True}}
    )


def unflag_user(username):
    """Remove flag from user"""
    users.update_one(
        {"_id": username},
        {"$set": {"flagged": False}}
    )


def reset_user_score(username):
    """Reset a user's score (admin action)"""
    users.update_one(
        {"_id": username},
        {
            "$set": {
                "total_score": 0,
                "cards_studied": 0,
                "correct_answers": 0,
                "incorrect_answers": 0,
                "current_streak": 0,
                "verification_passed": 0,
                "verification_failed": 0
            }
        }
    )


def get_leaderboard(limit=10):
    """Get top users by score (exclude flagged)"""
    return list(users.find({"flagged": {"$ne": True}}).sort("total_score", -1).limit(limit))