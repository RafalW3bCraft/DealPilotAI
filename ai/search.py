"""Small, explicit English/Hindi catalog vocabulary; no arbitrary substitutes."""

from __future__ import annotations

import re
import unicodedata

_STOP_WORDS = set('''a an and are as at be best below budget buy can choose do explain find
for from give i in is it me my need of on or please prefer product products recommend
recommendations show small some suggest that the this to under up useful want with your
max maximum less than not invent item items if unavailable display setup compact
के की का के लिए एक यह मुझे मेरी मेरे को में से और है हैं दिखाओ दिखाइए सुझाइए चाहिए उपयोगी घर'''.split())
_ALIASES = {
    'माउस': 'mouse', 'कीबोर्ड': 'keyboard', 'लैंप': 'lamp', 'लैम्प': 'lamp',
    'रोशनी': 'lamp', 'डेस्क': 'desk', 'मेज': 'desk', 'मेज़': 'desk',
    'ऑर्गनाइज़र': 'organizer', 'ऑर्गनाइजर': 'organizer', 'आयोजक': 'organizer',
    'केबल': 'cable', 'तार': 'cable', 'स्टैंड': 'stand', 'मॉनिटर': 'monitor',
    'पौधा': 'plant', 'पैड': 'pad', 'हेडफोन': 'headphones', 'हब': 'hub',
    'व्हाइटबोर्ड': 'whiteboard', 'बजट': '', 'तक': '', 'कम': '',
    'organiser': 'organizer', 'organization': 'organizer', 'organize': 'organizer',
    'tidy': 'organizer', 'lighting': 'lamp', 'headphone': 'headphones',
    'cables': 'cable', 'lamps': 'lamp', 'plants': 'plant', 'accessory': 'accessories',
    'office': 'desk', 'home': '', 'деск': 'desk',
}


def search_tokens(query: str) -> set[str]:
    text = unicodedata.normalize('NFC', query).casefold()
    words = re.findall(r'[\w\u0900-\u097f]+', text)
    return {
        _ALIASES.get(word, word)
        for word in words
        if word not in _STOP_WORDS and not word.isdecimal() and _ALIASES.get(word, word)
    }


def relevance(query: str, title: str, category: str, description: str = '') -> int:
    tokens = search_tokens(query)
    if not tokens:
        return 0
    title_tokens = search_tokens(title)
    category_tokens = search_tokens(category)
    description_tokens = search_tokens(description)
    return (len(tokens & title_tokens) * 4 + len(tokens & category_tokens) * 2
            + len(tokens & description_tokens))
