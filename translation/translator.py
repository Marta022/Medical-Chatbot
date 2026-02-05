from deep_translator import GoogleTranslator

def translate_to_romanian(chunks):
    """Translate chunks to Romanian (auto-detect source)."""
    translated = []
    for i, chunk in enumerate(chunks):
        try:
            translated_chunk = GoogleTranslator(source='auto', target='ro').translate(chunk)
            translated.append(translated_chunk)
        except Exception as e:
            print(f"Translation error for chunk {i}: {e}")
            translated.append(chunk)  # Keep original if translation fails
    return translated