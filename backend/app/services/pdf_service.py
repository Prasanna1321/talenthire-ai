"""
app/services/pdf_service.py
-------------------------------
Phase 7: generates a downloadable PDF interview report using reportlab
(pure Python, no system-level dependencies — unlike wkhtmltopdf/weasyprint,
so it installs cleanly on Windows via plain pip). Belongs in:
backend/app/services/pdf_service.py
"""

import io
from datetime import datetime
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable

BRAND_COLOR = colors.HexColor("#2f56f5")


def _recommendation_label(overall_score: Optional[float]) -> str:
    """
    Deterministic thresholds — same score always yields the same label.
    Documented here since the spec requires the recommendation be based on
    measurable performance, not an opaque/random choice.
    """
    if overall_score is None:
        return "Not Ready Yet"
    if overall_score >= 85:
        return "Strong Candidate"
    if overall_score >= 70:
        return "Good Potential"
    if overall_score >= 50:
        return "Needs Improvement"
    return "Not Ready Yet"


def generate_interview_report_pdf(
    candidate_name: str,
    job_title: Optional[str],
    ats_score: Optional[float],
    aptitude_percentage: Optional[float],
    average_interview_score: Optional[float],
    question_scores: list[dict],  # [{"question": str, "final_score": float}, ...]
    feedback: Optional[dict],  # {"strengths": str, "areas_to_improve": str, "detailed_feedback": str, "overall_rating": float}
    visual_metrics: Optional[dict] = None,
) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2 * cm, bottomMargin=2 * cm)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle("TitleBrand", parent=styles["Title"], textColor=BRAND_COLOR, fontSize=22)
    heading_style = ParagraphStyle("HeadingBrand", parent=styles["Heading2"], textColor=BRAND_COLOR, spaceBefore=14)
    body_style = styles["BodyText"]

    story = []
    story.append(Paragraph("TalentHire AI", title_style))
    story.append(Paragraph("Interview Evaluation Report", styles["Heading3"]))
    story.append(Spacer(1, 4))
    story.append(Paragraph(f"Candidate: <b>{candidate_name}</b>", body_style))
    if job_title:
        story.append(Paragraph(f"Role: {job_title}", body_style))
    story.append(Paragraph(f"Date: {datetime.now().strftime('%B %d, %Y')}", body_style))
    story.append(HRFlowable(width="100%", color=colors.lightgrey, spaceBefore=10, spaceAfter=10))

    # --- Score summary table ---
    story.append(Paragraph("Score Summary", heading_style))
    summary_data = [
        ["Metric", "Score"],
        ["Resume ATS Compatibility", f"{ats_score:.1f} / 100" if ats_score is not None else "N/A"],
        ["Aptitude Test", f"{aptitude_percentage:.1f}%" if aptitude_percentage is not None else "N/A"],
        ["Interview Score (avg)", f"{average_interview_score:.1f} / 100" if average_interview_score is not None else "N/A"],
    ]
    summary_table = Table(summary_data, colWidths=[9 * cm, 6 * cm])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BRAND_COLOR),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(summary_table)

    # --- Visual Observable Indicators ---
    if visual_metrics:
        story.append(Paragraph("Observable Visual Indicators", heading_style))
        vis_data = [
            ["Indicator", "Measurable Percentage"],
            ["Face Visibility", f"{visual_metrics.get('face_visibility', 0)}%"],
            ["Camera Orientation & Alignment", f"{visual_metrics.get('camera_orientation', 0)}%"],
            ["Posture Consistency", f"{visual_metrics.get('posture_consistency', 0)}%"],
        ]
        vis_table = Table(vis_data, colWidths=[9 * cm, 6 * cm])
        vis_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e0e7ff")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#1e1b4b")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(vis_table)

    # --- Question-wise scores ---
    if question_scores:
        story.append(Paragraph("Question-wise Evaluation", heading_style))
        qs_data = [["#", "Question", "Score"]]
        for i, q in enumerate(question_scores, start=1):
            question_text = q.get("question", "")[:90] + ("..." if len(q.get("question", "")) > 90 else "")
            qs_data.append([str(i), question_text, f"{q.get('final_score', 0):.1f}"])
        qs_table = Table(qs_data, colWidths=[1 * cm, 11 * cm, 2.5 * cm])
        qs_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8ecff")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(qs_table)

    # --- AI feedback ---
    if feedback:
        story.append(Paragraph("AI Feedback", heading_style))
        if feedback.get("strengths"):
            story.append(Paragraph("<b>Strengths:</b>", body_style))
            story.append(Paragraph(feedback["strengths"], body_style))
            story.append(Spacer(1, 6))
        if feedback.get("areas_to_improve"):
            story.append(Paragraph("<b>Areas to Improve:</b>", body_style))
            story.append(Paragraph(feedback["areas_to_improve"], body_style))
            story.append(Spacer(1, 6))
        if feedback.get("detailed_feedback"):
            story.append(Paragraph("<b>Detailed Feedback:</b>", body_style))
            story.append(Paragraph(feedback["detailed_feedback"], body_style))
            story.append(Spacer(1, 6))

    overall = feedback.get("overall_rating") if feedback else None
    overall_100_scale = (overall * 10) if overall is not None else average_interview_score
    recommendation = _recommendation_label(overall_100_scale)

    story.append(HRFlowable(width="100%", color=colors.lightgrey, spaceBefore=10, spaceAfter=10))
    story.append(Paragraph("Final Recommendation", heading_style))
    story.append(Paragraph(f"<b>{recommendation}</b>", ParagraphStyle("Rec", parent=body_style, fontSize=14, textColor=BRAND_COLOR)))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()
