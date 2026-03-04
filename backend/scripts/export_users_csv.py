import csv
import sys
from datetime import timezone

from backend.services.firebase import _get_app

SURVEY_COLUMNS = [
    "q1",
    "q2",
    "q3",
    "q4",
    "q5",
    "gender",
    "age",
    "survey_schema_version",
    "survey_submitted_at",
]


def _fmt_ts(ts) -> str:
    if ts is None:
        return ""
    try:
        dt = ts.astimezone(timezone.utc) if hasattr(ts, "astimezone") else ts
        return dt.isoformat()
    except Exception:
        return str(ts)


def _is_more_recent(a, b) -> bool:
    if b is None:
        return True
    if a is None:
        return False
    try:
        return a > b
    except Exception:
        return False


def load_survey_by_uid(db) -> dict[str, dict]:
    surveys: dict[str, dict] = {}
    for doc in db.collection("survey_responses").stream():
        data = doc.to_dict() or {}
        uid = data.get("uid")
        if not uid:
            continue
        submitted_at = data.get("submitted_at")
        existing = surveys.get(uid)
        if existing is None or _is_more_recent(submitted_at, existing.get("_submitted_at")):
            surveys[uid] = {
                "answers": data.get("answers", {}),
                "schema_version": data.get("schema_version", ""),
                "_submitted_at": submitted_at,
                "submitted_at_str": _fmt_ts(submitted_at),
            }
    return surveys


def _parse_topics(doc_dict: dict) -> dict:
    if "topics" in doc_dict and isinstance(doc_dict["topics"], dict):
        return doc_dict["topics"]
    # Fallback: treat the whole dict as topics (legacy / manual uploads).
    return {k: v for k, v in doc_dict.items() if isinstance(v, dict)}


def aggregate_difficulties(topics: dict) -> dict[str, dict[str, int]]:
    result: dict[str, dict[str, int]] = {}
    for diffs in topics.values():
        for difficulty, counts in diffs.items():
            totals = result.setdefault(difficulty, {"attempts": 0, "correct": 0, "hints": 0})
            totals["attempts"] += counts.get("attempts", 0)
            totals["correct"] += counts.get("correct", 0)
            totals["hints"] += counts.get("hints", 0)
    return result


def main() -> None:
    output_path = sys.argv[1] if len(sys.argv) > 1 else "users_export.csv"

    print("Initialising Firebase Admin SDK...")
    _get_app()
    from firebase_admin import firestore

    db = firestore.client()

    print("Loading survey responses...")
    surveys = load_survey_by_uid(db)
    print(f"  {len(surveys)} unique users with survey responses")

    print("Loading user models...")
    user_rows: list[tuple[str, dict[str, dict[str, int]]]] = []
    all_difficulties: set[str] = set()

    for doc in db.collection("user_models").stream():
        uid = doc.id
        by_difficulty = aggregate_difficulties(_parse_topics(doc.to_dict() or {}))
        all_difficulties.update(by_difficulty.keys())
        user_rows.append((uid, by_difficulty))

    print(f"  {len(user_rows)} users, {len(all_difficulties)} unique difficulties")

    sorted_difficulties = sorted(all_difficulties)
    difficulty_columns = [f"{d}_{stat}" for d in sorted_difficulties for stat in ("attempts", "correct", "hints")]
    fieldnames = ["uid"] + difficulty_columns + SURVEY_COLUMNS

    print(f"Writing CSV to {output_path}...")
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for uid, by_difficulty in user_rows:
            row: dict = {"uid": uid}

            # Difficulty columns — fill zeros for difficulties the user hasn't touched.
            for difficulty in sorted_difficulties:
                stats = by_difficulty.get(difficulty, {"attempts": 0, "correct": 0, "hints": 0})
                row[f"{difficulty}_attempts"] = stats["attempts"]
                row[f"{difficulty}_correct"] = stats["correct"]
                row[f"{difficulty}_hints"] = stats["hints"]

            # Survey columns.
            survey = surveys.get(uid)
            if survey:
                answers = survey["answers"]
                row.update(
                    {
                        "q1": answers.get("1", ""),
                        "q2": answers.get("2", ""),
                        "q3": answers.get("3", ""),
                        "q4": answers.get("4", ""),
                        "q5": answers.get("5", ""),
                        "gender": answers.get("gender", ""),
                        "age": answers.get("age", ""),
                        "survey_schema_version": survey["schema_version"],
                        "survey_submitted_at": survey["submitted_at_str"],
                    }
                )
            else:
                row.update({k: "" for k in SURVEY_COLUMNS})

            writer.writerow(row)

    print(f"Done. {len(user_rows)} rows → {output_path}")


if __name__ == "__main__":
    main()
