from __future__ import annotations

try:
    from deep_translator import GoogleTranslator
except ModuleNotFoundError:
    class GoogleTranslator:  # type: ignore[override]
        def __init__(self, source: str = "auto", target: str = "en") -> None:
            self.source = source
            self.target = target

        def translate(self, text: str) -> str:
            return text


def translate_to_english(text: str) -> str:
    cleaned = (text or "").strip()
    if not cleaned:
        return cleaned
    return GoogleTranslator(source="auto", target="en").translate(cleaned)


def translate_to_romanian(items: list[str]) -> list[str]:
    if not items:
        return []

    translator = GoogleTranslator(source="auto", target="ro")
    translated: list[str] = []
    for item in items:
        cleaned = (item or "").strip()
        translated.append(translator.translate(cleaned) if cleaned else cleaned)
    return translated
