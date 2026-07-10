# Input Parsing And Confidence Rules

Use this file for PDF, DOCX, pasted text, OCR, or screenshots. Content evidence quality and layout evidence quality are separate.

## Evidence Ladder

| Source | `layout_evidence` | Presentation cap | Max presentation confidence | Content use |
|---|---|---:|---|---|
| Text extracted plus rendered pages inspected | `rendered_file` | 100 | high | Score content normally when extraction is complete. |
| Reliable file structure without full visual inspection | `file_structure` | 90 | high | Score content normally; avoid exact visual claims. |
| Reliable extracted text only | `extracted_text` | 82 | medium | Score content normally; infer only structural layout signals. |
| Complete pasted text/Markdown | `pasted_text` | 75 | medium | Score content normally; do not claim fonts, margins, or visual polish. |
| Partial/noisy OCR | `ocr_only` | 65 | low | Lower content confidence; avoid strong conclusions. |

The presentation cap never caps `career_capital`, `communication_quality`, or `core_score` when text is complete.

## PDF

1. Extract text with layout preservation when possible.
2. Compare extraction order with rendered page order.
3. Check copyability, image-only text, columns, tables, and reading order.
4. If extraction is incomplete, list missing sections and lower affected-axis confidence rather than inventing content.

## DOCX

1. Extract text with an available DOCX/XML parser.
2. Check tables used for layout, text boxes, floating shapes, and header/footer-only contact details.
3. When rendering is unavailable, use `file_structure` or `extracted_text` and avoid exact visual claims.

## Pasted Text

- Score career capital and communication normally when content is complete.
- Use only section order, heading clarity, line/bullet structure, and textual ATS labels for communication.
- Use only cautious structural signals for presentation and obey the 75 cap.

## Screenshots And OCR

- Prefer the original file or pasted text.
- Use `ocr_only` and low confidence when OCR is partial or noisy.
- Do not turn unreadable or cropped content into negative career-capital evidence.

## Downgrade Rules

- Missing layout evidence lowers only presentation confidence/cap.
- Missing target lowers positioning confidence; it does not erase demonstrated experience value.
- Missing ownership or result context lowers evidence coverage and the directly affected dimension only.
- Parser failure is not a resume weakness.
- Never infer private details or hidden metrics from metadata.
