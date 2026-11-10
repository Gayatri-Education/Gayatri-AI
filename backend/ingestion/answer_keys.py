"""Attach public-source proposals without overwriting reviewed keys."""

import hashlib
import json
from sqlalchemy import select
from backend.config import DATA_DIR
from backend.models import Question

KEY_DIR = DATA_DIR / "answer_keys" / "neet"


def read_ledger(directory=KEY_DIR):
    document = json.loads((directory / "answer_ledger.json").read_text())
    if document.get("schema_version") != 1:
        raise ValueError("Unsupported answer ledger schema")
    rows = document["questions"]
    sources = {
        s["id"]: s
        for s in json.loads((directory / "sources.json").read_text())["sources"]
    }
    seen = set()
    for row in rows:
        if row["question_id"] in seen:
            raise ValueError("Duplicate question in answer ledger")
        seen.add(row["question_id"])
        choices = row["accepted_options"]
        if len(set(choices)) != len(choices) or any(
            k not in "ABCD" or len(k) != 1 for k in choices
        ):
            raise ValueError("Invalid accepted options in answer ledger")
        if row["status"] != "sourced_candidate" and choices:
            raise ValueError(
                "Unresolved/conflicting records must not have a selected answer"
            )
        if row.get("published"):
            raise ValueError(
                "Research ledger cannot publish keys; use explicit reviewer approval"
            )
        for evidence in row["evidence"]:
            source = sources.get(evidence["source_id"])
            if (
                evidence["kind"] == "official_key_mirror"
                and evidence["accepted_options"]
                and len(evidence["option_mapping"]) != 4
            ):
                raise ValueError(
                    "A partial OCR option mapping cannot transfer an official-mirror key"
                )
            if not source or evidence["source_url"] != source["url"]:
                raise ValueError("Unrecognized or changed source citation")
            if (
                not source["url"].startswith("https://raw.githubusercontent.com/")
                or len(source["sha256"]) != 64
            ):
                raise ValueError("Invalid immutable source reference")
    return rows


def import_answer_keys(db, directory=KEY_DIR):
    rows = read_ledger(directory)
    questions = {q.external_id: q for q in db.scalars(select(Question))}
    report = {"attached": 0, "preserved_approved": 0, "stale_or_missing": 0}
    for row in rows:
        q = questions.get(row["question_id"])
        if (
            not q
            or hashlib.sha256(q.text.encode()).hexdigest() != row["question_sha256"]
        ):
            report["stale_or_missing"] += 1
            continue
        if q.approved:
            report["preserved_approved"] += 1
            continue
        metadata = json.loads(q.metadata_json)
        metadata["sourced_answer"] = row
        q.metadata_json = json.dumps(metadata)
        # Only prefill an unambiguous candidate. This does not approve it or
        # make it eligible for a scored paper. Conflicts explicitly have no key.
        q.correct_option = (
            row["accepted_options"][0] if row["accepted_options"] else None
        )
        citations = list(
            dict.fromkeys(
                e["source_url"] + " (" + e["locator"] + ")"
                for e in row["evidence"]
                if e["accepted_options"] == row["accepted_options"]
                and row["accepted_options"]
            )
        )
        q.answer_key_source = "\n".join(citations[:3])
        q.explanation = ""  # A published choice is not a verified explanation.
        report["attached"] += 1
    db.flush()
    return report


def approved_options(question):
    """Preserve compatibility with old single-key reviews and reject stale metadata."""
    if (
        not question.approved
        or not question.correct_option
        or question.correct_option not in "ABCD"
    ):
        return []
    info = json.loads(question.metadata_json).get("approved_answer", {})
    choices = info.get("accepted_options", [])
    fingerprint = hashlib.sha256(question.text.encode()).hexdigest()
    if (
        info.get("question_sha256") == fingerprint
        and question.correct_option in choices
        and all(k in "ABCD" and len(k) == 1 for k in choices)
    ):
        return choices
    return [question.correct_option]
