from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


def build_report(job_id: str, transcript: str, summary: str, action_items: str, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(output_path), pagesize=letter,
        rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72,
    )
    styles = getSampleStyleSheet()
    story = [Paragraph("<b>VoiceScribe AI Meeting Report</b>", styles["Title"]), Spacer(1, 0.2 * inch)]

    story.append(Paragraph("Summary", styles["Heading2"]))
    story.append(Paragraph(summary or "No summary available.", styles["BodyText"]))
    story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph("Action Items & Decisions", styles["Heading2"]))
    story.append(Paragraph(action_items or "No action items extracted.", styles["BodyText"]))
    story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph("Transcript", styles["Heading2"]))
    for line in transcript.split("\n"):
        story.append(Paragraph(line, styles["BodyText"]))
        story.append(Spacer(1, 0.05 * inch))

    doc.build(story)
    return output_path
