from __future__ import annotations

from config.settings import BASE_SYSTEM_PROMPT

GUARDRAIL_SYSTEM_PROMPT = (
    "Esti un filtru de siguranta pentru un chatbot medical. "
    "Raspunde doar cu una dintre etichete: EMERGENCY, UNSAFE, SAFE. "
    "Foloseste EMERGENCY pentru simptome sau situatii critice care pot pune viata in pericol "
    "(de ex. durere in piept, dificultati severe de respiratie, pierdere de constiinta, "
    "sangerare masiva, semne de AVC, supradoza, anafilaxie, arsuri grave). "
    "Foloseste UNSAFE pentru solicitari periculoase sau interzise "
    "(auto-vatamare, violenta fata de altii, fabricare droguri, solicitari de diagnostic sigur, "
    "prescriptii sau doze exacte). "
    "Solicitarile generale de informare (definitii, simptome generale, cauze, prevenire, "
    "complicatii) sunt SAFE daca nu descriu o urgenta. "
    "Daca nu esti sigur, alege EMERGENCY cand pare urgent, altfel UNSAFE. "
    "Raspunde doar cu eticheta."
)

CONTEXT_BLOCK_HEADER = "Top similar diseases and additional information:"
LOW_CONFIDENCE_MESSAGE = (
    "Nu am suficiente informatii relevante pentru a raspunde cu siguranta. "
    "Te rog consulta un medic sau reformuleaza intrebarea."
)
PDF_MARKDOWN_CLEANUP_SYSTEM_PROMPT = (
    "You are a medical-document formatting assistant. "
    "Convert extracted PDF page text into clean Markdown while preserving the original content as closely as possible. "
    "Fix obvious encoding artifacts (for example mojibake such as ÅŸ/Å£/Äƒ/Ã¢/Ã®) into correct Romanian characters. "
    "Keep headings and list structure when clearly present. "
    "Keep output language in Romanian only (no translation to English). "
    "Do not invent sections or rewrite content beyond formatting and obvious cleanup. "
    "Remove obvious garbage fragments/tokens that are non-lexical noise (for example random symbol clusters), "
    "but keep valid medical abbreviations, units, numbers, and terminology. "
    "Use clean, readable Markdown structure: one main title first, then clear section headings and lists only when they are explicit in source. "
    "Do not create malformed headings or list markers (for example empty '-', '1.', or heading lines without meaningful text). "
    "Do not force numbered lists when numbering is unclear; prefer plain paragraphs or bullet lists when structure is uncertain. "
    "If a fragment is unreadable/noisy, keep the original fragment as plain text instead of inventing missing words. "
    "Do not invent facts, sections, or medical claims not found in the source text. "
    "Output Markdown only."
)


def get_base_system_prompt() -> str:
    return BASE_SYSTEM_PROMPT


def build_context_block(context_lines: list[str]) -> str:
    return CONTEXT_BLOCK_HEADER + "\n" + "\n".join(f"- {line}" for line in context_lines)


def build_pdf_markdown_cleanup_user_message(
    *,
    source_file: str,
    page_number: int,
    page_text: str,
) -> str:
    return (
        f"Source file: {source_file}\n"
        f"Page: {page_number}\n\n"
        "Task:\n"
        "- Clean broken PDF line wrapping while preserving wording and facts.\n"
        "- Keep headings and list items when they exist.\n"
        "- Avoid malformed markdown: no empty headings, no empty list items, no forced numbering if unclear.\n"
        "- If text is unclear, keep it as plain text without inventing missing words.\n"
        "- Keep Romanian language only. Do not translate or paraphrase into another language.\n"
        "- Remove only obvious garbage tokens; keep medical terms/abbreviations/numbers.\n"
        "- Return valid Markdown only.\n\n"
        "Extracted page text:\n"
        f"{page_text.strip()}"
    )
