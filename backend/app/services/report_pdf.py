from __future__ import annotations

import unicodedata

from fpdf import FPDF

from ..schemas.report import ForensicReport


def render_report_pdf(report: ForensicReport) -> bytes:
    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=16)
    pdf.add_page()
    pdf.set_title(f"Forensic report - {report.incident.data.incident_id}")
    pdf.set_author("SpillTrack Forensic API")

    def write_line(text: str, height: float = 6) -> None:
        text = text.translate(
            str.maketrans(
                {
                    "\u2012": "-",
                    "\u2013": "-",
                    "\u2014": " - ",
                    "\u2018": "'",
                    "\u2019": "'",
                    "\u201c": '"',
                    "\u201d": '"',
                    "\u2026": "...",
                    "\u00a0": " ",
                }
            )
        )
        text = unicodedata.normalize("NFKD", text).encode("ascii", "replace").decode("ascii")
        pdf.multi_cell(0, height, text, new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "B", 16)
    write_line("Oil Spill Forensic Report", 9)
    pdf.set_font("Helvetica", size=10)
    write_line(f"Incident: {report.incident.data.incident_id}")
    write_line(f"Title: {report.incident.data.title}")
    write_line(f"Generated: {report.generated_at.isoformat()}")
    write_line(f"Incident source: {report.incident.provenance.source}")
    pdf.ln(3)

    if report.detection is not None:
        pdf.set_font("Helvetica", "B", 12)
        write_line("Detection", 7)
        pdf.set_font("Helvetica", size=10)
        write_line(
            f"Scene: {report.detection.data.scene_id}; classification: "
            f"{report.detection.data.classification}; confidence: "
            f"{report.detection.data.oil_confidence:.2f}",
        )

    if report.hindcast is not None:
        pdf.set_font("Helvetica", "B", 12)
        write_line("Hindcast artifact", 7)
        pdf.set_font("Helvetica", size=10)
        write_line(
            f"Origin center: {report.hindcast.data.center}; radius: "
            f"{report.hindcast.data.radius_km} km; model: {report.hindcast.data.model}",
        )
        if report.hindcast.data.is_fallback:
            write_line("WARNING: deterministic development fallback, not a scientific forecast.")

    pdf.set_font("Helvetica", "B", 12)
    write_line("Attribution assessment", 7)
    pdf.set_font("Helvetica", size=10)
    write_line(f"Outcome: {report.attribution.data.attribution.outcome.value}")
    write_line(str(report.attribution.data.attribution.message))
    dossier = report.attribution.data.dossier
    if dossier is not None:
        write_line(dossier.headline)
        for line in dossier.lines:
            write_line(f"{line.tag}: {line.text}")
        write_line(str(dossier.verdict))

    pdf.set_font("Helvetica", "B", 12)
    write_line(f"Evidence events ({len(report.evidence.data)})", 7)
    pdf.set_font("Helvetica", size=10)
    if report.evidence.data:
        for event in report.evidence.data:
            write_line(
                f"{event.occurred_at.isoformat()} [{event.kind.value}] "
                f"{event.description} (source: {event.source_ref})"
            )
    else:
        write_line("No persisted evidence events are available.")

    for unavailable in report.unavailable_artifacts:
        write_line(str(unavailable))

    content = pdf.output()
    return bytes(content) if isinstance(content, bytearray) else content