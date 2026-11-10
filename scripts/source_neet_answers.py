"""Fetch pinned public evidence and build a question-by-question answer ledger.

No scraped code is executed. Source data and PDFs stay in ignored var/. Only
factual answer mappings, hashes, citations and match diagnostics are committed.
Requires requirements-research.txt, pdftotext and (for the scanned paper) OCR tools.
"""

import argparse
import csv
import hashlib
import html
import json
import os
import re
import subprocess
import unicodedata
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests
from rapidfuzz import fuzz, process

ROOT = Path(__file__).resolve().parents[1]
BANK = ROOT / "data/question_bank/neet"
OUTPUT = ROOT / "data/answer_keys/neet"
LETTERS = "ABCD"


def plain(value):
    value = re.sub(r"<(style|script)\b[^>]*>.*?</\1>", " ", value, flags=re.I | re.S)
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"\[image:[^\]]+\]", " ", value)
    return unicodedata.normalize("NFKC", html.unescape(value)).strip()


def stem_normal(value):
    return re.sub(r"[^\w]", "", plain(value).casefold())


def option_normal(value):
    value = (
        plain(value).casefold().replace("−", "-").replace("–", "-").replace("×", "*")
    )
    # Keep signs, decimal points, units and numbers. 4.4 mT must never equal 44 mT.
    return re.sub(r"[^\w+*/=<>.%\-]", "", value)


def parse_options(text):
    labels = list(re.finditer(r"\(([1-4])\)", text))
    if [m[1] for m in labels] != list("1234"):
        return text, {}
    options = {}
    for i, match in enumerate(labels):
        end = labels[i + 1].start() if i < 3 else len(text)
        options[LETTERS[i]] = text[match.end() : end].strip()
    return text[: labels[0].start()], options


def parse_key(value):
    parts = re.split(r"\s*(?:,|\bor\b)\s*", str(value).lower().strip())
    lookup = dict(zip("1234abcd", "ABCDABCD"))
    if not parts or any(p not in lookup for p in parts):
        return []
    return sorted(set(lookup[p] for p in parts))


def option_mapping(target_options, source_options):
    scores = {}
    for target_letter, text in target_options.items():
        if "[image:" in text:
            continue
        normalized = option_normal(text)
        if not normalized:
            continue
        ranked = []
        for source_letter, value in source_options.items():
            candidate = option_normal(value)
            # Numerical disagreement is not a formatting difference.
            if re.findall(r"\d+(?:\.\d+)?", candidate) != re.findall(
                r"\d+(?:\.\d+)?", normalized
            ):
                continue
            ranked.append((fuzz.ratio(normalized, candidate) / 100, source_letter))
        ranked.sort(reverse=True)
        if (
            ranked
            and ranked[0][0] == 1.0
            and sum(score == 1.0 for score, _ in ranked) == 1
        ):
            scores[target_letter] = {
                "source_option": ranked[0][1],
                "similarity": round(ranked[0][0], 4),
            }
    values = [v["source_option"] for v in scores.values()]
    if len(set(values)) != len(values):
        return {}  # Never infer an option from a non-bijective mapping.
    return scores


def fetch(source, cache, offline):
    path = cache / (source["id"] + Path(source["path"]).suffix)
    if not path.exists():
        if offline:
            raise ValueError(f"Missing cached evidence: {source['id']}")
        response = requests.get(source["url"], timeout=60)
        response.raise_for_status()
        content = response.content
        if hashlib.sha256(content).hexdigest() != source["sha256"]:
            raise ValueError(f"Source checksum mismatch: {source['id']}")
        path.write_bytes(content)
    if hashlib.sha256(path.read_bytes()).hexdigest() != source["sha256"]:
        raise ValueError(f"Cached evidence checksum mismatch: {source['id']}")
    return path


def pdf_text(path):
    return subprocess.check_output(["pdftotext", "-layout", str(path), "-"], text=True)


def read_sources(manifest, paths):
    records = []
    for source in manifest["sources"]:
        kind, sid = source["kind"], source["id"]
        path = paths[sid]
        if kind == "community_bank":
            for index, row in enumerate(json.loads(path.read_text())):
                # This source includes erroneous header fragments under blank years.
                if not row.get("year") or not row.get("question"):
                    continue
                stem, options = parse_options(row["question"])
                records.append(
                    {
                        "source_id": sid,
                        "locator": f"row[{index}]",
                        "year": int(row["year"]),
                        "subject": row["subject"],
                        "stem": stem,
                        "options": options,
                        "answers": parse_key(row.get("correct_answer")),
                        "number": row.get("question_number"),
                        "kind": kind,
                    }
                )
        elif kind == "structured_paper":
            for section in json.loads(path.read_text()):
                for q in section.get("questions", []):
                    subject = q.get("subject", "").title()
                    if subject in {"Botany", "Zoology"}:
                        subject = "Biology"
                    records.append(
                        {
                            "source_id": sid,
                            "locator": q["question_id"],
                            "year": source["year"],
                            "subject": subject,
                            "stem": q["content"],
                            "options": {
                                o["identifier"]: o["content"]
                                for o in q.get("options", [])
                            },
                            "answers": q.get("correct_options", []),
                            "kind": kind,
                            "bonus": q.get("isBonus", False),
                        }
                    )
        elif kind == "solution_paper":
            content = pdf_text(path)
            # Check the actual title, rather than trusting the path's year.
            if "NEET (UG)-2024" not in content or "2026 Free Mock" in content:
                raise ValueError(f"Unexpected solution document title: {sid}")
            starts = list(re.finditer(r"^\s*(\d{1,3})\.\s", content, re.M))
            found = set()
            for index, match in enumerate(starts):
                end = (
                    starts[index + 1].start()
                    if index + 1 < len(starts)
                    else len(content)
                )
                chunk = content[match.end() : end]
                answer = re.search(r"Answer\s*\(([^)]+)\)", chunk)
                if not answer:
                    continue
                number = int(match[1])
                found.add(number)
                stem, options = parse_options(chunk[: answer.start()])
                records.append(
                    {
                        "source_id": sid,
                        "locator": f"question:{number}",
                        "year": source["year"],
                        "subject": "Physics"
                        if number <= 50
                        else "Chemistry"
                        if number <= 100
                        else "Biology",
                        "stem": stem,
                        "options": options,
                        "answers": parse_key(answer[1]),
                        "number": number,
                        "kind": kind,
                        "page": content[: match.start()].count("\f") + 1,
                    }
                )
            if found != set(range(1, 201)):
                raise ValueError(f"Incomplete solution extraction: {sid}")
    return records


def evidence(record, target, similarity, sources):
    mapping = option_mapping(
        {k: target["option_" + k.lower()] for k in LETTERS}, record["options"]
    )
    inverse = {v["source_option"]: k for k, v in mapping.items()}
    accepted = [inverse.get(k) for k in record["answers"]]
    if not accepted or not all(accepted):
        accepted = []
    source = sources[record["source_id"]]
    return {
        "source_id": record["source_id"],
        "source_url": source["url"],
        "locator": record["locator"],
        "source_year": record["year"],
        "source_subject": record["subject"],
        "source_question_number": record.get("number"),
        "source_answer_options": record["answers"],
        "accepted_options": sorted(set(accepted)),
        "option_mapping": mapping,
        "stem_similarity": round(similarity, 4),
        "source_stem_sha256": hashlib.sha256(
            plain(record["stem"]).encode()
        ).hexdigest(),
        "kind": record["kind"],
        "bonus": record.get("bonus", False),
        "page": record.get("page"),
    }


def ocr_paper(path, cache, offline, expected_pages):
    directory = cache / "ocr-paper45"
    directory.mkdir(exist_ok=True)
    texts = sorted(directory.glob("page-*.txt"))
    if not texts:
        if offline:
            raise ValueError("Missing scanned-paper OCR cache")
        subprocess.run(
            [
                "pdftoppm",
                "-scale-to",
                "2400",
                "-png",
                str(path),
                str(directory / "page"),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
        )
        pages = sorted(directory.glob("page-*.png"))

        def run(page):
            subprocess.run(
                ["tesseract", str(page), str(page.with_suffix("")), "--psm", "3"],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                env=os.environ | {"OMP_THREAD_LIMIT": "1"},
            )

        with ThreadPoolExecutor(max_workers=4) as pool:
            list(pool.map(run, pages))
        texts = sorted(directory.glob("page-*.txt"))
    if len(texts) != 32:
        raise ValueError("Expected 32 OCR pages for the pinned code-45 paper")
    for page in texts:
        if hashlib.sha256(page.read_bytes()).hexdigest() != expected_pages.get(
            page.name
        ):
            raise ValueError(
                f"OCR evidence differs from the reviewed source extraction: {page.name}"
            )
    return [p.read_text() for p in texts]


def norm_with_positions(text):
    normalized, positions = [], []
    for index, character in enumerate(text):
        for c in unicodedata.normalize("NFKC", character).casefold():
            if c.isalnum() or c == "_":
                normalized.append(c)
                positions.append(index)
    return "".join(normalized), positions


def official_mirror_candidates(targets, metadata, paths, sources, cache, offline):
    key_text = pdf_text(paths["nta-2025-key-mirror"])
    first = key_text.split("\f")[0]
    if not re.search(r"FINAL ANSWER KEY.*2025", first) or not re.search(
        r"Test Booklet Code\s*:\s*45", first
    ):
        raise ValueError("Wrong final answer-key title or booklet code")
    keys = {}
    for line in first.splitlines():
        for number, answer in re.findall(
            r"(?<![\d.])(\d{1,3})\s+([1-4](?:\s*,\s*[1-4])*)(?=\s|$)", line
        ):
            number = int(number)
            if number in keys:
                raise ValueError("Duplicate question in the code-45 final key")
            keys[number] = parse_key(answer)
    if set(keys) != set(range(1, 181)) or not all(keys.values()):
        raise ValueError("Incomplete official-mirror key parsing")
    pages = ocr_paper(
        paths["neet-2025-paper45"],
        cache,
        offline,
        sources["neet-2025-paper45"]["ocr_pages"],
    )
    normalized = [norm_with_positions(p) for p in pages]
    if sum("45english" in text.replace("_", "") for text, _ in normalized) < 15:
        raise ValueError("Could not confirm code 45 across scanned-paper pages")
    alignments = {}
    for i, target in enumerate(targets):
        if target["year"] != "2025":
            continue
        needle = stem_normal(target["question"])
        best = None
        for page, (haystack, positions) in enumerate(normalized):
            alignment = fuzz.partial_ratio_alignment(needle, haystack)
            if best is None or alignment.score > best[0]:
                best = (alignment.score, page, alignment)
        alignments[i] = best
    result = {}
    for i, (score, page, alignment) in alignments.items():
        target = targets[i]
        number = int(metadata[i]["printed_question_number"])
        normalized_page, positions = normalized[page]
        if alignment.dest_end == 0:
            continue
        start = positions[alignment.dest_end - 1] + 1
        later = [
            other.dest_start
            for j, (s, p, other) in alignments.items()
            if j != i
            and p == page
            and s >= 85
            and other.dest_start >= alignment.dest_end
        ]
        end = positions[min(later)] if later else len(pages[page])
        region = pages[page][start:end]
        _, options = parse_options(region)
        if not options:
            labels = list(re.finditer(r"\(([1-4])\)", region))
            if len(labels) > 4 and [m[1] for m in labels[:4]] == list("1234"):
                _, options = parse_options(region[: labels[4].start()])
        record = {
            "source_id": "nta-2025-key-mirror",
            "locator": f"booklet:45;question:{number}",
            "year": 2025,
            "subject": target["subjects"],
            "stem": target["question"],
            "options": options,
            "answers": keys[number],
            "number": number,
            "kind": "official_key_mirror",
            "page": 1,
        }
        item = evidence(record, target, score / 100, sources)
        # OCR can place a printed label after its text (notably code-45 Q62).
        # A partial apparent match can therefore assign the correct wording to
        # the wrong label. Require all four options before transferring any key.
        if len(item["option_mapping"]) != 4:
            item["accepted_options"] = []
            item["option_mapping_incomplete"] = True
        item["paper_source_id"] = "neet-2025-paper45"
        item["paper_page"] = page + 1
        item["paper_link_method"] = (
            "booklet_45_printed_number_plus_stem_and_option_alignment"
        )
        item["source_stem_sha256"] = (
            None  # OCR score is against the paper, not an exact text extraction.
        )
        item["notes"] = [
            "Official-labelled key mirror; direct NTA download was blocked. Number transfer alone is never sufficient for publication."
        ]
        # Retain published source answers even when this target's option mapping is unresolved.
        result[i] = item
    return result


def build(manifest, paths, cache, offline):
    with (BANK / "neet_pyq.csv").open(encoding="utf-8-sig", newline="") as f:
        targets = list(csv.DictReader(f))
    with (BANK / "question_metadata.csv").open(encoding="utf-8-sig", newline="") as f:
        metadata = list(csv.DictReader(f))
    sources = {s["id"]: s for s in manifest["sources"]}
    records = read_sources(manifest, paths)
    corpus = [stem_normal(r["stem"]) for r in records]
    official = official_mirror_candidates(
        targets, metadata, paths, sources, cache, offline
    )
    ledger = []
    for index, target in enumerate(targets):
        needle = stem_normal(target["question"])
        matches = process.extract(
            needle, corpus, scorer=fuzz.ratio, score_cutoff=75, limit=12
        )
        candidates = []
        for _, similarity, source_index in matches:
            record = records[source_index]
            if record["subject"] != target["subjects"] or not record["answers"]:
                continue
            candidates.append(evidence(record, target, similarity / 100, sources))
        if index in official:
            candidates.append(official[index])
        mapped = [
            c
            for c in candidates
            if c["accepted_options"]
            and c["stem_similarity"] >= 0.85
            and c["source_year"] == int(target["year"])
            and not c["bonus"]
        ]
        outcomes = {tuple(c["accepted_options"]) for c in mapped}
        accepted = list(next(iter(outcomes))) if len(outcomes) == 1 else []
        status = (
            "conflict"
            if len(outcomes) > 1
            else "sourced_candidate"
            if accepted
            else "mapping_required"
            if candidates
            else "no_source_match"
        )
        # Exact-alignment keys are still proposals for a reviewer, not an automatic
        # scientific correctness certificate. No community source auto-approves.
        ledger.append(
            {
                "question_id": metadata[index]["question_id"],
                "question_sha256": metadata[index]["question_sha256"],
                "year": int(target["year"]),
                "subject": target["subjects"],
                "status": status,
                "accepted_options": accepted,
                "review_flags": metadata[index]["review_flags"],
                "evidence": candidates,
                "published": False,
            }
        )
    return ledger


def write(ledger):
    (OUTPUT / "answer_ledger.json").write_text(
        json.dumps(
            {"schema_version": 1, "questions": ledger}, ensure_ascii=False, indent=2
        )
        + "\n"
    )
    summary = {
        "question_count": len(ledger),
        "counts_by_status": dict(Counter(r["status"] for r in ledger)),
        "published_count": sum(r["published"] for r in ledger),
        "by_year": {
            str(year): dict(Counter(r["status"] for r in ledger if r["year"] == year))
            for year in range(2015, 2027)
        },
        "policy": "Publicly sourced proposals only. No candidate bypasses answer-key/source-image review. Conflicts and unmapped options remain unresolved.",
    }
    (OUTPUT / "coverage_report.json").write_text(json.dumps(summary, indent=2) + "\n")
    with (OUTPUT / "answer_keys.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(
            [
                "question_id",
                "question_sha256",
                "year",
                "subject",
                "status",
                "accepted_options",
                "source_ids",
            ]
        )
        for row in ledger:
            writer.writerow(
                [
                    row["question_id"],
                    row["question_sha256"],
                    row["year"],
                    row["subject"],
                    row["status"],
                    "|".join(row["accepted_options"]),
                    "|".join(sorted({e["source_id"] for e in row["evidence"]})),
                ]
            )
    print(json.dumps(summary, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--offline", action="store_true", help="Use checksum-verified local cache only"
    )
    parser.add_argument("--cache", type=Path, default=ROOT / "var/answer-source-cache")
    args = parser.parse_args()
    args.cache.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((OUTPUT / "sources.json").read_text())
    paths = {s["id"]: fetch(s, args.cache, args.offline) for s in manifest["sources"]}
    write(build(manifest, paths, args.cache, args.offline))


if __name__ == "__main__":
    main()
