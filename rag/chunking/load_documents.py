from __future__ import annotations

import csv
import json
from pathlib import Path

from models import MedicalItem


def _validate_json_structure(data: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, list):
        return ["JSON root must be a list of categories."]

    for cat_index, category in enumerate(data, start=1):
        if not isinstance(category, dict):
            errors.append(f"Category #{cat_index} must be an object.")
            continue
        name = (category.get("name") or "").strip()
        if not name:
            errors.append(f"Category #{cat_index} missing 'name'.")
        diseases = category.get("diseases")
        if diseases is None:
            errors.append(f"Category '{name or cat_index}' missing 'diseases' list.")
            continue
        if not isinstance(diseases, list):
            errors.append(f"Category '{name or cat_index}' diseases must be a list.")
            continue
        for disease_index, disease in enumerate(diseases, start=1):
            if not isinstance(disease, dict):
                errors.append(f"Disease #{disease_index} in category '{name}' must be an object.")
                continue
            title = (disease.get("name") or "").strip()
            description = (disease.get("description") or "").strip()
            symptoms = (disease.get("symptoms") or "").strip()
            if not any([title, description, symptoms]):
                errors.append(
                    f"Disease #{disease_index} in category '{name}' must have name, description, or symptoms."
                )
    return errors


def _is_csv_header(row: list[str]) -> bool:
    if len(row) < 2:
        return False
    first = row[0].strip().lower()
    second = row[1].strip().lower()
    return ("disease" in first or "symptom" in first) and (
        "cure" in second or "treatment" in second
    )


def load_medical_items(json_path: str, csv_path: str) -> list[MedicalItem]:
    items: list[MedicalItem] = []
    errors: list[str] = []

    json_file = Path(json_path)
    csv_file = Path(csv_path)
    if not json_file.exists():
        raise FileNotFoundError(f"JSON file not found: {json_path}")
    if not csv_file.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    with json_file.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    errors.extend(_validate_json_structure(data))

    if isinstance(data, list):
        for category in data:
            if not isinstance(category, dict):
                continue
            cat = (category.get("name") or "").strip()
            for disease in category.get("diseases", []):
                if not isinstance(disease, dict):
                    continue
                name = (disease.get("name") or "").strip()
                description = (
                    f"Category: {cat}\n"
                    f"Description: {disease.get('description', '')}\n"
                    f"Transmission: {disease.get('transmission', '')}\n"
                    f"Symptoms: {disease.get('symptoms', '')}\n"
                    f"Treatment: {disease.get('treatment', '')}\n"
                    f"Complications: {disease.get('complications', '')}\n"
                    f"Prevention: {disease.get('prevention', '')}\n"
                ).strip()
                if not name and not description:
                    continue
                items.append(
                    MedicalItem(
                        title=name,
                        description=description,
                        source="json",
                        category=cat,
                    )
                )

    with csv_file.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        header_checked = False
        for row_index, row in enumerate(reader, start=1):
            if not row:
                continue
            if not header_checked:
                header_checked = True
                if _is_csv_header(row):
                    continue
            if len(row) < 2:
                errors.append(f"CSV row #{row_index} must have at least 2 columns.")
                continue
            disease_and_symptoms = row[0].strip()
            cure = row[1].strip()
            if not disease_and_symptoms or not cure:
                errors.append(f"CSV row #{row_index} has empty required fields.")
                continue
            description = f"Disease+Symptoms: {disease_and_symptoms}\nCure: {cure}"
            items.append(
                MedicalItem(
                    title="",
                    description=description.strip(),
                    source="csv",
                )
            )

    if errors:
        raise ValueError("Dataset validation failed:\n- " + "\n- ".join(errors))

    if not items:
        raise ValueError("No valid medical items loaded from dataset files.")

    return items
