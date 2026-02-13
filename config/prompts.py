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


def get_base_system_prompt() -> str:
    return BASE_SYSTEM_PROMPT


def build_context_block(context_lines: list[str]) -> str:
    return CONTEXT_BLOCK_HEADER + "\n" + "\n".join(f"- {line}" for line in context_lines)

