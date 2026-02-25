from __future__ import annotations

from deep_translator import GoogleTranslator


def translate_to_romanian(chunks: list[str]) -> list[str]:
    translated: list[str] = []
    for chunk in chunks:
        translated_chunk = GoogleTranslator(source="auto", target="ro").translate(chunk)
        translated.append(translated_chunk)
    return translated


def translate_to_english(text: str) -> str:
    return GoogleTranslator(source="auto", target="en").translate(text)
