"""
PARROT-AI memes — Giphy search integration.

GIF queries updated for v1.0: no more bird GIFs (opponents weaponized them).
"""
from __future__ import annotations

import os
import random
import requests

GIPHY_API_KEY = os.getenv("GIPHY_API_KEY", "").strip()
GIPHY_SEARCH_URL = "https://api.giphy.com/v1/gifs/search"

# v1.0: no bird queries. opponents used them as ammunition.
MOOD_QUERIES = {
    "ragequit":   ["mic drop", "walking away", "door slam", "peace out"],
    "angry":      ["fire", "mad", "frustrated", "steam"],
    "victory":    ["crown", "winner", "champion", "trophy"],
    "praise":     ["confused", "suspicious", "side eye", "hmm"],
    "insult":     ["fight", "boxing", "mic drop", "popcorn"],
    "neutral":    ["typing", "computer", "sassy", "shrug"],
    "late_night": ["sleepy", "tired", "sleeping", "yawn"],
    "meta_roast": ["magnifying glass", "detective", "thinking"],
    "copium":     ["copium", "cope", "denial"],
    "backhanded": ["fake smile", "side eye", "eye roll"],
}


def _search_giphy(query: str, limit: int = 5) -> list[str]:
    if not GIPHY_API_KEY:
        return []
    try:
        r = requests.get(GIPHY_SEARCH_URL, params={
            "api_key": GIPHY_API_KEY,
            "q": query,
            "limit": limit,
            "rating": "pg-13",
        }, timeout=5)
        if r.status_code != 200:
            return []
        data = r.json().get("data", [])
        urls = []
        for item in data:
            url = item.get("images", {}).get("downsized", {}).get("url")
            if url:
                urls.append(url)
        return urls
    except Exception:
        return []


def pick_gif(mood: str) -> str | None:
    if not GIPHY_API_KEY:
        return None
    queries = MOOD_QUERIES.get(mood) or MOOD_QUERIES["neutral"]
    query = random.choice(queries)
    urls = _search_giphy(query)
    return random.choice(urls) if urls else None