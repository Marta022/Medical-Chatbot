def _score_prediction(
    predicted: set[str],
    gold: set[str],
) -> dict[str, float | int | bool]:
    """Compute per-item set metrics for benchmark answers."""

    true_positive = len(predicted & gold)
    false_positive = len(predicted - gold)
    false_negative = len(gold - predicted)

    precision = true_positive / len(predicted) if predicted else 0.0
    recall = true_positive / len(gold) if gold else 1.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )

    return {
        "tp": true_positive,
        "fp": false_positive,
        "fn": false_negative,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "exact_match": predicted == gold,
    }
