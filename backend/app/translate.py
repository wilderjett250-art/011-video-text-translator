COMMON_TRANSLATIONS = {
    "klever live": "Klever 直播",
    "every week": "每周直播",
    "last story": "最后故事",
    "youtube": "YouTube",
    "facebook": "Facebook",
    "instagram": "Instagram",
    "tiktok": "TikTok",
    "whatnot": "Whatnot",
}


def suggest_translation(text: str) -> str:
    normalized = " ".join(text.strip().lower().split())
    return COMMON_TRANSLATIONS.get(normalized, text.strip())

