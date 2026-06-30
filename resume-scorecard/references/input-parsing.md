# Input Parsing And Confidence Rules

Use this file when the resume comes from PDF, DOCX, pasted text, OCR, or screenshots. The goal is not to mandate one parser; it is to make evidence quality explicit before scoring.

## Preferred Evidence Ladder

| Evidence Level | Use When | `layout_evidence` | Presentation Confidence | Suggested Presentation Cap |
|---|---|---|---|---:|
| Rendered file | Full text is extracted and at least the first page or whole document can be visually inspected. | `rendered_file` | `high` | 100 |
| File structure | PDF/DOCX text and section order are reliable, but visual rendering is incomplete. | `file_structure` | `medium` or `high` | 90 |
| Extracted text | Text extraction preserves section order but not visual layout. | `extracted_text` | `medium` | 82 |
| Pasted text | User pasted text/Markdown only. | `pasted_text` | `low` or `medium` | 75 |
| OCR only | OCR is partial, noisy, or from screenshots. | `ocr_only` | `low` | 65 |

If the evidence level would cap the presentation score below the score you want to give, lower the score or state why the cap is overridden in `presentation_review.summary`. Do not use `high` confidence for pasted text.

## PDF Handling

1. Extract text with layout preservation when possible, such as `pdftotext -layout`, a PDF text library, or the available PDF/document tools in the current environment.
2. Compare extracted order against the visual page order when a page preview or screenshot is available.
3. Inspect whether text is copyable, whether the resume is image-only, and whether columns/tables disturb reading order.
4. If extraction returns little text, treat the file as OCR/image-like and ask for a text export before assigning a full content score.

## DOCX Handling

1. Extract text with `textutil`, `python-docx`, or a DOCX/XML parser available in the environment.
2. Check structural hazards: tables used for layout, text boxes, floating shapes, header/footer-only contact details, and inconsistent heading styles.
3. When visual rendering is unavailable, score content normally from reliable text, but keep `presentation_review.layout_evidence` at `file_structure` or `extracted_text`.

## Pasted Text / Markdown

- Score content normally if the text is complete.
- Use structural signals only for presentation: section order, heading clarity, line length, bullet density, repeated date patterns, and obvious ATS labels.
- Do not claim margins, font quality, exact spacing, or visual polish from pasted text alone.

## Screenshot Or Image Input

- Do not score content from screenshots alone unless text is OCR-readable and the user accepts lower confidence.
- Use `ocr_only`, `low` confidence, and a conservative presentation score.
- Ask for the original PDF/DOCX/text when the screenshot is incomplete or contains unreadable details.

## Failure And Downgrade Rules

- If a parser fails but another source provides complete text, proceed with content scoring and mark missing layout evidence.
- If only partial text is available, lower overall `confidence` and list the missing sections.
- If file layout evidence is missing, include `presentation_review.layout_evidence` and obey the suggested cap.
- Never infer private contact details or hidden metrics from file metadata.
