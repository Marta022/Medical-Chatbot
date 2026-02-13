from llm_hub.router import llm_classify

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


def classify_guardrail_with_llm(query):
    response = llm_classify(
        messages=[
            {"role": "system", "content": GUARDRAIL_SYSTEM_PROMPT},
            {"role": "user", "content": query},
        ],
        temperature=0,
    )

    if not response:
        return "SAFE"

    label = response.strip().upper()
    if label in ("EMERGENCY", "UNSAFE", "SAFE"):
        return label

    # Fallback: try to recover from verbose output
    if "EMERGENCY" in label:
        return "EMERGENCY"
    if "UNSAFE" in label:
        return "UNSAFE"

    return "SAFE"
