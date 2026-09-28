from __future__ import annotations

import json
import os
from functools import lru_cache
from typing import Any

from google import genai
from google.genai import types
from pydantic import BaseModel

from .file_extract import ExtractedDocument


NOT_IDENTIFIED = "Not Identified"


class ReportData(BaseModel):
    title: str = NOT_IDENTIFIED
    activity_type: str = NOT_IDENTIFIED
    brief_information: str = NOT_IDENTIFIED
    profile_topic: str = NOT_IDENTIFIED
    objective: str = NOT_IDENTIFIED
    methodology: str = NOT_IDENTIFIED
    outcome: str = NOT_IDENTIFIED
    proposal_date: str = NOT_IDENTIFIED
    activity_date: str = NOT_IDENTIFIED
    time: str = NOT_IDENTIFIED
    faculty: str = NOT_IDENTIFIED
    department_committee_association: str = NOT_IDENTIFIED
    venue: str = NOT_IDENTIFIED
    participants: str = NOT_IDENTIFIED
    activity_for_class_group: str = NOT_IDENTIFIED
    coordinator_name_phone: str = NOT_IDENTIFIED
    members_support: str = NOT_IDENTIFIED
    resource_person: str = NOT_IDENTIFIED
    invited_guest: str = NOT_IDENTIFIED
    iqac_cell_activity_number: str = NOT_IDENTIFIED
    activity_schedule_number: str = NOT_IDENTIFIED
    event_report: str = NOT_IDENTIFIED

    # Proof/checklist detection for the second page of the IQAC Summary template.
    proposal_present: bool = False
    notice_present: bool = False
    programme_present: bool = False
    invitation_present: bool = False
    attendance_present: bool = False
    event_report_evidence_present: bool = False
    feedback_present: bool = False
    news_present: bool = False
    publicity_present: bool = False
    certificate_present: bool = False
    other_evidence_present: bool = False


SYSTEM_PROMPT = """
You are an expert college IQAC report preparation assistant.
Read ALL supplied documents and images as one activity packet and reconcile the facts.
The user is preparing two official reports from the college's supplied templates.

CORE RULES
1. Extract facts from the documents; never invent names, dates, times, venues, counts,
   outcomes, guests or organizations.
2. Use contextual extraction. Information does not need to have the exact field label.
   Read paragraphs, tables, headings, signatures, notices, proposals and letters together.
3. If a fact is genuinely unavailable, return exactly: Not Identified.
4. Prefer the most specific and authoritative statement when documents differ.
5. Preserve actual names, dates, times and numbers exactly as supported.

RESOURCE PERSON / INVITATION LETTER
When a Letter of Invitation or Appreciation is supplied, inspect it carefully for the
resource person's full name, designation, speaker/guest role or invited expert. Populate
resource_person with the person's name and designation when stated. If several resource
persons are clearly named, list them separated by semicolons. Do not confuse the organizer,
principal, coordinator or committee member with a resource person unless the document
explicitly describes that person in that role.
If resource_person is identified, invited_guest may also contain the same person when the
IQAC template field "Name of Invited Guest (Optional)" is appropriate.

PROOF / CHECKLIST DETECTION
The IQAC Summary page 2 contains a checklist. Mark each boolean TRUE only when the
corresponding document/evidence is actually present in the supplied packet.
Use both the document filename and its actual text/image contents. A generic filename is
not enough if the content clearly identifies another document type.
- proposal_present: signed/duly signed proposal or proposal document
- notice_present: notice/circular/announcement of the activity
- programme_present: table program/schedule/programme
- invitation_present: letter of invitation and/or appreciation letter
- attendance_present: attendance/participant list or attendance sheet
- event_report_evidence_present: event report and/or geotagged photographic evidence
- feedback_present: feedback form, feedback summary or feedback analysis
- news_present: news clipping/news photo/news item
- publicity_present: publicity/reel/social media/news link evidence
- certificate_present: certificate/sample certificate
- other_evidence_present: other supporting evidence that does not fit the categories above
Do not mark an item true merely because the activity description mentions it.

CONTENT FIELDS
brief_information <= 180 characters
profile_topic <= 120 characters
objective <= 220 characters
methodology <= 90 characters
outcome <= 180 characters
members_support <= 120 characters
resource_person <= 160 characters
event_report should be a factual, polished narrative of 100-150 words, using only supported
facts. Include the resource person when the invitation/appreciation letter supports it.

activity_type should be a concise institutional category such as Curricular, Co-Curricular,
Extra-Curricular, Extension, Society-based, Commemorative Day, or another clearly supported category.

Return only the structured result.
"""


@lru_cache(maxsize=1)
def _client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured.")
    return genai.Client(api_key=api_key)


def _model() -> str:
    return os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")


def _build_contents(docs: list[ExtractedDocument], vision_images: list[Any]) -> list[Any]:
    context_parts: list[str] = []
    for d in docs:
        context_parts.append(f"===== {d.name} ({d.kind}) =====\n{d.text[:40000]}")
    user_prompt = SYSTEM_PROMPT + "\n\nACTIVITY PACKET:\n" + "\n\n".join(context_parts)
    contents: list[Any] = [user_prompt]
    for image in vision_images[:12]:
        contents.append(image)
    return contents


def extract_report_data(docs: list[ExtractedDocument], vision_images: list[Any]) -> ReportData:
    client = _client()
    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=ReportData,
        temperature=0.1,
    )
    response = client.models.generate_content(
        model=_model(),
        contents=_build_contents(docs, vision_images),
        config=config,
    )
    parsed = getattr(response, "parsed", None)
    if isinstance(parsed, ReportData):
        return parsed
    text = getattr(response, "text", "") or ""
    if not text:
        raise RuntimeError("Gemini returned an empty response.")
    return ReportData.model_validate(json.loads(text))
