from __future__ import annotations

"""Keyword and phrase groups used by deterministic guardrail checks."""

EMERGENCY_PATTERN_GROUPS: dict[str, list[str]] = {
    "cardiovascular": [
        "durere in piept",
        "durere puternica in piept",
        "presiune in piept",
        "infarct",
        "atac cardiac",
    ],
    "breathing": [
        "nu pot respira",
        "nu pot sa respir",
        "respir greu",
        "respiratie foarte grea",
        "dificultati de respiratie",
        "sufoc",
    ],
    "neurological": [
        "accident vascular",
        "avc",
        "atac cerebral",
        "fata cazuta pe o parte",
        "nu pot vorbi",
        "confuzie brusca",
        "convulsii",
        "pierdere brusca a vederii",
    ],
    "bleeding_trauma": [
        "sangerare masiva",
        "sangerare severa",
        "sangerare care nu se opreste",
        "hemoragie",
        "fractura deschisa",
        "trauma grava",
        "ranit grav",
    ],
    "overdose_poisoning": [
        "supradoza",
        "otravire",
        "otravit",
        "am inghitit otrava",
        "am luat prea multe pastile",
        "reactie alergica severa",
        "anafilaxie",
        "soc anafilactic",
    ],
}

UNSAFE_CRITICAL_PATTERN_GROUPS: dict[str, list[str]] = {
    "self_harm": [
        "vreau sa ma sinucid",
        "cum sa ma sinucid",
        "ma sinucid",
        "nu mai vreau sa traiesc",
        "cum sa imi fac rau",
        "imi fac rau",
        "ma tai",
        "suicid",
        "sinucidere",
    ],
    "violence": [
        "vreau sa omor",
        "cum omor pe cineva",
        "cum ranesc pe cineva",
        "cum sa fac rau altcuiva",
    ],
    "drug_synthesis": [
        "cum fac droguri",
        "cum prepar droguri",
        "amestec droguri",
        "cum se face heroina",
        "cum se face metamfetamina",
        "cum fac cocaina",
    ],
}

UNSAFE_SOFT_PATTERN_GROUPS: dict[str, list[str]] = {
    "dosage_prescription": [
        "doza exacta",
        "doza precisa",
        "doza exacta pentru",
        "prescrie-mi",
        "antibiotic fara reteta",
        "medicamente fara reteta",
        "ce antibiotic sa iau exact",
    ],
    "medical_certainty": [
        "diagnostic sigur",
        "tratament exact",
        "tratament personalizat",
        "schema de tratament",
        "schema exacta",
    ],
}

SAFE_INFO_PATTERNS: list[str] = [
    "ce este",
    "ce inseamna",
    "definitie",
    "care sunt simptomele",
    "ce simptome",
    "cauze",
    "factori de risc",
    "preventie",
    "prevenire",
    "complicatii",
    "tratament",
]

EDUCATIONAL_FRAMING_PATTERNS: list[str] = [
    "ce este",
    "ce inseamna",
    "definitie",
    "explica",
    "simptome",
    "simptomele",
    "care sunt simptomele",
    "care sunt cauzele",
    "cum se manifesta",
]

FIRST_PERSON_SYMPTOM_MARKERS: list[str] = [
    "am durere",
    "am febra",
    "am tuse",
    "am ameteli",
    "ma doare",
    "simt ca",
    "ma simt",
    "imi este rau",
    "am observat ca",
    "sufar de",
    "am simptome",
]

URGENCY_MARKERS: list[str] = [
    "acum",
    "urgent",
    "de urgenta",
    "sever",
    "foarte grav",
    "dintr-o data",
]
