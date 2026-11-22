# Public-source answer research

Research performed on 10 November 2026 against all **2,240** uploaded records. This is **not a complete verified answer key**. Eighteen immutable GitHub-hosted source files were inspected. All citations pin a full commit and SHA-256 checksum. The checked-in ledger contains factual answer proposals and matching diagnostics; downloaded third-party datasets, papers, solution text and OCR artifacts remain in ignored `var/answer-source-cache/`.

## Coverage

| Research outcome | Questions | Portal behavior |
| --- | ---: | --- |
| Unambiguous source proposal | 947 | Prefilled draft key, with citations; still unapproved |
| Conflicting mapped keys | 74 | No selected answer; competing sources shown |
| Question/option mapping unresolved | 889 | Source facts retained; no target key selected |
| No reliable accessible match | 330 | No answer supplied |
| Total | 2,240 | Every original ID and exact question hash retained |

**No answer was automatically approved.** This preserves the existing scoring contract. A public repository is not itself an official correctness certificate. Proposed answers appear in post-submission study review with an unverified label and in the admin review workflow. They are hidden during an active attempt and never affect a grade. Runtime human approvals are stored in the database separately from the research ledger's `published_count=0`.

## Sources and cautions

The complete inventory is [sources.json](../data/answer_keys/neet/sources.json).

- [Community NEET dataset](https://github.com/abdulwahid947040-ctrl/Neet-pyq-datasets-) supplies structured answer proposals for 2018–2024. Blank-year/header records were excluded. Its keys contain demonstrable mistakes; it is never an automatic approval source.
- [JEENEETards](https://github.com/skndash96/jeeneetards) contains older NEET/AIPMT papers and question/option keys. Its README attributes content to Examside, Examsnet and other sources; the repository does not establish ownership of those questions. Only factual key mappings and references are retained here.
- [ALL-PYQ-Papers](https://github.com/Shabber10/ALL-PYQ-Papers) mirrors Aakash's 5 May 2024 Q1/T1 solutions. These are coaching solutions, not the revised NTA final answer key. Two booklet codes from one publisher are not independent corroboration. A PDF filed there under `NEET/2022/...solution.pdf` actually identifies itself as a **2026 free mock test** and was excluded.
- [CBT portal repository](https://github.com/AshutoshJena07/CBT-portal-for-NEET-) mirrors an NTA-labelled **2025 final answer key**, with codes 45–48, and a scanned code-45 paper. The key's first page contains all 180 code-45 answers and accepts either option 1 or 2 on question 63. Direct NTA access was blocked, so this remains explicitly described as a mirror. Matching the paper code or printed number alone never approves an answer.

A real conflict is `NEET_2024_PHYSICS_001`: the community dataset assigns **4.4 T**, while both Aakash code variants solve the coil question as **4.4 mT**. Their option letters differ between booklets, so the matcher maps by option content rather than transferring letters or question numbers.

A real OCR trap is `NEET_2025_CHEMISTRY_062`: OCR of the scanned source puts some printed labels after their option text. Partial matching can associate the right words with the wrong label. This row remains unresolved. A key from an OCR paper is transferred only when all four option identities match exactly. The uploaded source image also contains a wording difference from the mirrored paper in one option; the original upload is retained unchanged.

## How matching works

Question stems produce candidate matches; these similarity scores describe text identity, **not scientific answer confidence**. Option transfer requires a unique, exact canonical option-content match. Signs, decimals, units and numerical tokens are retained: `-30 J` differs from `30 J`, and `4.4 mT` differs from `44 mT`. Image-only options are never guessed. Missing/bonus/dropped key markers are never coerced to option A. Conflicting answers, year mismatches and incomplete source-label mappings remain unresolved.

Every proposal attaches to an exact original `question_sha256`. Import skips missing or edited questions and never overwrites an already approved key. An administrator must inspect the question image and citation, resolve all source conflicts, provide a verified explanation and explicitly confirm review. For multiple accepted choices, check all accepted choices and include the primary displayed choice. Either accepted response earns full credit; students still select one option. Immutable paper snapshots retain the entire accepted set so a subsequent review cannot change a past result. Existing single-key snapshots remain compatible.

## Reproduce or extend

```bash
.venv/bin/pip install -r requirements-research.txt
# Requires trusted installations of pdftotext, pdftoppm and tesseract (English).
.venv/bin/python -m scripts.source_neet_answers
# Recheck cached evidence without network:
.venv/bin/python -m scripts.source_neet_answers --offline
# Attach proposals to the runtime bank without approving them:
.venv/bin/python -m scripts.seed_db
```

Source downloads keep normal TLS verification enabled. Bytes must match the pinned checksums before use. OCR page checksums, tool version and parameters are recorded too; a changed extraction is a reason to review the evidence, not to silently replace expected hashes. The checked-in ledger was regenerated from the checksum-validated cache; a full fresh download/OCR run has not been independently repeated.

Outputs:

- `data/answer_keys/neet/answer_keys.csv`: one status/key/provenance row per uploaded question.
- `answer_ledger.json`: detailed citations, source keys, mapped choices and alignment diagnostics.
- `coverage_report.json`: per-year counts of resolved proposals and unresolved categories.
- `sources.json`: immutable public URLs, source hashes, provenance, excluded sources and blocked destinations.

## What is still needed to finish all questions

The environment permits GitHub but denies direct access to `neet.nta.nic.in`, `exams.nta.ac.in`, `nta.ac.in`, `www.nta.ac.in`, and `cdnbbsr.s3waas.gov.in`. Google and the GitHub API were blocked too. Saving a network-access draft failed with `INVALID_ARGUMENT`; no access change is confirmed saved or applied. Enable the required official sites in environment settings, including any actual PDF redirect hosts, or supply the corresponding verified final-key PDFs with booklet codes. Then re-check each question/option identity. Existing citations and unresolved rows make that work resumable.

In particular, the uploaded 2026 filenames do not establish paper authenticity, and no dependable 2026 key has been located in the accessible sources. The remaining 330 unmatched rows and 889 mapping cases cannot responsibly be filled with guesses or generated answers.
