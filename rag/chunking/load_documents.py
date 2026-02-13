from __future__ import annotations

import csv
import json

from models import MedicalItem


def load_medical_items(json_path: str, csv_path: str) -> list[MedicalItem]:
    items: list[MedicalItem] = []

    with open(json_path, "r", encoding="utf-8") as handle:
        data = json.load(handle)

    for category in data:
        cat = category.get("name")
        for disease in category.get("diseases", []):
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
            items.append(
                MedicalItem(
                    title=name,
                    description=description,
                    source="json",
                    category=cat,
                )
            )

    with open(csv_path, "r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        for row in reader:
            if len(row) < 2:
                continue
            disease_and_symptoms = row[0].strip()
            cure = row[1].strip()
            description = f"Disease+Symptoms: {disease_and_symptoms}\nCure: {cure}"
            items.append(
                MedicalItem(
                    title="",
                    description=description.strip(),
                    source="csv",
                )
            )

    return items

