# NEET PYQ dataset, 2015-2026

2,240 questions extracted from the 12 supplied PDFs. The year follows the supplied filename. This conversion does not independently authenticate the papers.

## Main CSV

`neet_pyq.csv` uses exactly this column order:

`question,subjects,difficulty,option_a,option_b,option_c,option_d,year`

The CSVs use UTF-8 with a BOM, standard double-quote escaping, and CRLF record separators. Quoted question and option cells can contain line breaks. Use a CSV reader rather than splitting lines or commas. Subjects are Physics, Chemistry, or Biology, following the paper's subject sections.

## Images and mapping

- `diagrams/`: 627 question images containing diagrams, graphs, chemical structures, tables, other visual content, or options needing an image. The complete question context is retained to preserve labels and image-only choices. Automatic visual detection may also include contextual images without a diagram.
- `question_images/`: source snapshots for the remaining questions. Every CSV record has a readable source snapshot across these two folders.
- `diagram_map.csv`: maps diagram images to CSV records and relevant option fields.
- `image_map.csv`: maps every source image to its CSV record.
- `question_metadata.csv`: question IDs, source PDF/page(s), printed question numbers, extraction methods, confidence, image paths, review flags, difficulty-estimate reasons, and crop coordinates in PDF points.
- `review_required.csv`: records with OCR, option, formula-layout, or source-numbering checks.

`csv_row` is the one-based DATA RECORD number, excluding the header; it is not a physical file line number because fields can contain line breaks. `question_sha256` hashes the exact question string in the main CSV and supports matching after sorting. `question_id` is unique within this package. Image paths are relative to this directory. Extract the ZIP before following them.

The main CSV references relevant images as `[image: diagrams/2018/NEET_2018_PHYSICS_001.png]`, for example. When an option is an image or its text was not recognized, its cell contains the image reference and option letter. Those cells are not invented transcriptions. All four printed choices remain visible in the source snapshots, subject to the quality of the supplied scans.

## Extraction and review

Embedded PDF text was used where available. Image-only pages were rendered and processed with English OCR, with additional question-level OCR and alternate passes for difficult scans. Multi-column layouts and questions continued onto another column/page were joined. Separately printed answer keys and the 2025 text-solution section were excluded. Original PDFs are not included in this archive.

Review is still needed for imperfect OCR, subscripts, superscripts, fractions, symbols, chemical notation, and dense tables. A simple stacked numeric fraction was normalized to `numerator/denominator`; more complex formula text should be checked against its source image. OCR confidence measures recognition confidence, not scientific correctness. A record without a flag has not necessarily been manually verified.

483 option cells across 219 records use image references. These include both inherently graphical choices and unrecognized text. 633 records have one or more review flags, including formula-layout checks; the counts overlap.

The 2015 first question has faint source print. The 2021 Biology source prints question number 35 twice and has no printed 34 in that sequence; both questions are retained under distinct IDs. Printed numbering is preserved in metadata rather than silently deleting or merging either question.

## Difficulty estimates

Difficulty is an automated estimate, not an official NEET rating or a measured solve rate. The heuristic uses the stem's numerical content, matching/statements, linked-step wording, visual interpretation, and length. Easy indicates direct recall or identification; Moderate indicates application, matching, numerical work, or a visual task; Hard indicates multiple such indicators. The specific indicators used are recorded in `difficulty_estimate_basis` in the metadata. The questions were not solved to validate these labels.

## Coverage

| Year | Questions |
| --- | ---: |
| 2015 | 180 |
| 2016 | 180 |
| 2017 | 180 |
| 2018 | 180 |
| 2019 | 180 |
| 2020 | 180 |
| 2021 | 200 |
| 2022 | 200 |
| 2023 | 200 |
| 2024 | 200 |
| 2025 | 180 |
| 2026 | 180 |
| Total | 2240 |

Subject totals: Physics 560; Chemistry 560; Biology 1120.
