import json
import csv

def load_medical_items(json_path, csv_path):
    items = []

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for category in data:
        cat = category.get("name")
        for d in category.get("diseases", []):
            name = (d.get("name") or "").strip()

            description = (
                f"Category: {cat}\n"
                f"Description: {d.get('description','')}\n"
                f"Transmission: {d.get('transmission','')}\n"
                f"Symptoms: {d.get('symptoms','')}\n"
                f"Treatment: {d.get('treatment','')}\n"
                f"Complications: {d.get('complications','')}\n"
                f"Prevention: {d.get('prevention','')}\n"
            ).strip()

            items.append({
                "title": name,
                "description": description,
                "source": "json",
                "category": cat,
            })

    with open(csv_path, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()

    for line in lines:
        left, right = line.split(",", 1)

        disease_and_symptoms = left.strip()
        cure = right.strip().strip('"')

        text = (
        "Disease+Symptoms: " + disease_and_symptoms + "\n"
        "Cure: " + cure
        ).strip()

        items.append({
        "title": disease_and_symptoms,
        "description": text,
        "source": "csv",
        })

    return items
