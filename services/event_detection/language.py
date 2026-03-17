"""Language detection and translation layer for multi-lingual event detection.

Detects input language; if non-English, optionally translates to English
for downstream classification. Falls back to pass-through if translation
is unavailable.
"""

from typing import Optional, Tuple

from utils.logger import logger

_detector = None


def _get_detector():
    global _detector
    if _detector is None:
        try:
            import langdetect
            _detector = langdetect
            logger.info("langdetect_available")
        except ImportError:
            _detector = False
            logger.warning("langdetect_not_installed", hint="pip install langdetect")
    return _detector


def detect_language(text: str) -> Tuple[str, float]:
    """Detect language of text. Returns (lang_code, confidence)."""
    if not text or len(text.strip()) < 20:
        return "en", 0.5

    det = _get_detector()
    if det is False:
        return "en", 0.5

    try:
        from langdetect import detect_langs
        langs = detect_langs(text[:1000])
        if langs:
            top = langs[0]
            return top.lang, top.prob
    except Exception as e:
        logger.debug("langdetect_failed", error=str(e))
    return "en", 0.5


def is_english(text: str) -> bool:
    """Quick check: is text primarily English?"""
    lang, conf = detect_language(text)
    return lang == "en" and conf >= 0.5


def prepare_text_for_classification(text: str) -> Tuple[str, str]:
    """Prepare text for event classification. Returns (text, detected_lang).
    Translation is opt-in via config; for now we pass through.
    """
    lang, _ = detect_language(text)
    return text, lang
