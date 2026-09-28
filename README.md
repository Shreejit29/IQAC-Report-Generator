# IQAC Report Generator

A standalone Streamlit application for generating the college's **Event Report** and **IQAC Summary Report** from Notices, Proposals, supporting documents, and photographs.

This is a **separate application** from IQAC Analyzer.

## User workflow

1. Upload Notice and Proposal.
2. Optionally upload supporting documents.
3. Upload Geotagged Photos, Normal Photos and News Photos separately.
4. Click **Extract Activity Details**.
5. Review/edit the extracted information.
6. Click **Generate Event Report + IQAC Summary Report**.
7. Download two editable `.docx` files.

## Templates

The two official RTCCS templates are bundled unchanged under `templates/`:

- `Event report with geotagged photos and news.docx`
- `Revised IQAC Report Format 2026-27.docx`

The generator fills the templates rather than creating a redesigned report.

## Secrets

For Streamlit Cloud, add:

```toml
GEMINI_API_KEY = "your-key"
GEMINI_MODEL = "gemini-3.5-flash-lite"
```

`GEMINI_MODEL` is optional; the code uses its default when omitted.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Recent updates
- Added dedicated **Letter of Invitation / Appreciation** upload.
- The AI now extracts the **Resource Person** (name/designation) from invitation/appreciation material and uses it in the review and IQAC Summary's invited-guest field.
- The IQAC Summary page-2 **Proofs Attached** table is populated from the actual uploaded documents plus AI document-type detection; unsupported categories are not automatically ticked.
- Generated content is formatted in **Times New Roman, 12 pt** while the supplied template structure, header, tables, signatures and page layout are retained.
