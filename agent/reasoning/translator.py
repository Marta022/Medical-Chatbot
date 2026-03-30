from __future__ import annotations

"""Translation helpers used in chat orchestration flows."""

try:
    from deep_translator import GoogleTranslator
except ModuleNotFoundError:

    class GoogleTranslator:  # type: ignore[override]
        """Fallback translator that returns input unchanged when dependency is missing."""

        def __init__(self, source: str = "auto", target: str = "en") -> None:
            self.source = source
            self.target = target

        def translate(self, text: str) -> str:
            return text


SOURCE_LANGUAGE = "auto"
TARGET_ENGLISH = "en"
TARGET_ROMANIAN = "ro"


def translate_to_english(text: str) -> str:
    """Translate a single string to English, preserving empty input."""

    cleaned = (text or "").strip()
    if not cleaned:
        return cleaned
    return GoogleTranslator(source=SOURCE_LANGUAGE, target=TARGET_ENGLISH).translate(cleaned)


def translate_to_romanian(items: list[str]) -> list[str]:
    """Translate a list of strings to Romanian while preserving empty items."""

    if not items:
        return []

    translator = GoogleTranslator(source=SOURCE_LANGUAGE, target=TARGET_ROMANIAN)
    translated: list[str] = []
    for item in items:
        cleaned = (item or "").strip()
        translated.append(translator.translate(cleaned) if cleaned else cleaned)
    return translated
