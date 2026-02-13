from deep_translator import GoogleTranslator

def translate_to_romanian(chunks):
    """Translate chunks to Romanian."""
    translated = []
    for i, chunk in enumerate(chunks):
        translated_chunk = GoogleTranslator(source='auto', target='ro').translate(chunk)
        translated.append(translated_chunk)  
    return translated


def translate_to_english(text):
    """Translate text to English."""
    return GoogleTranslator(source='auto', target='en').translate(text)
