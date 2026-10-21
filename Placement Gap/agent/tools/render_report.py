from __future__ import annotations

import json
from collections.abc import Mapping
from io import BytesIO
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

from agent.state import RunState


def render_report(state: RunState, out: Path) -> dict[str, str]:
    out.mkdir(parents=True, exist_ok=True)
    reqs = {r.skill_id: r for r in state.requirements}
    lines = [
        f"# PlacementGap report — {state.student_id}",
        "",
        f"JD discovery tier: **{state.discovery_tier}**",
        "",
        "## Executive summary",
        f"{len(state.gaps)} skill gaps assessed; {sum(g.verdict != 'has' for g in state.gaps)} need work. Weekly budget: {state.hours_per_week:g} hours for {state.weeks} weeks.",
        "",
        "## Gap table",
        "| Requirement | Verdict | Delta | Evidence |",
        "|---|---|---:|---|",
    ]
    for g in state.gaps:
        req = reqs.get(g.skill_id)
        refs = []
        if req and req.evidence:
            refs.append(f"[JD:{req.evidence.char_span[0]}-{req.evidence.char_span[1]}]")
        refs.extend(f"[{e.source_doc_id}:{e.char_span[0]}-{e.char_span[1]}]" for e in g.evidence)
        ev = "; ".join(refs) or "No profile evidence"
        lines.append(
            f"| {req.skill_text if req else g.skill_id} | {g.verdict} | {g.level_delta} | {ev} |"
        )
    lines += ["", "## Week-by-week plan"]
    for w in range(1, state.weeks + 1):
        lines += [f"### Week {w}"]
        for p in state.plan:
            if p.week == w:
                lines.append(
                    f"- {p.skill_id}: {p.hours:g}h — {p.objective}"
                    + (
                        f" (deferred: {p.deferred_reason})"
                        if p.status == "deferred"
                        else "; resources: " + ", ".join(p.resources)
                    )
                )
    lines += ["", "## Deferred items"]
    deferred = [p for p in state.plan if p.status == "deferred"]
    lines.extend([f"- {p.skill_id}: {p.deferred_reason}" for p in deferred] or ["None."])
    lines += ["", "## Provenance appendix"]
    for i, g in enumerate(state.gaps, 1):
        req = reqs.get(g.skill_id)
        if req and req.evidence:
            e = req.evidence
            lines.append(
                f"[{i}] Job description chars {e.char_span[0]}–{e.char_span[1]}: “{e.quote}” (confidence {e.extractor_confidence:.2f})"
            )
        for e in g.evidence:
            lines.append(
                f"[{i}] {e.source_doc_id} chars {e.char_span[0]}–{e.char_span[1]}: “{e.quote}” (confidence {e.extractor_confidence:.2f})"
            )
    if state.degraded:
        lines += ["", "## Reduced scope", *["- " + x for x in state.degraded_reasons]]
    md = "\n".join(lines) + "\n"
    (out / "report.md").write_text(md, encoding="utf-8")
    payload = {
        "run_id": state.run_id,
        "student_id": state.student_id,
        "degraded": state.degraded,
        "requirements": [r.model_dump(mode="json") for r in state.requirements],
        "gaps": [g.model_dump(mode="json") for g in state.gaps],
        "plan": [p.model_dump(mode="json") for p in state.plan],
        "trace": [t.model_dump(mode="json") for t in state.trace],
        "markdown": md,
    }
    (out / "report.json").write_text(
        json.dumps(payload, indent=2, default=lambda x: x.__dict__), encoding="utf-8"
    )
    _render_pdf(state, reqs, out / "report.pdf")
    return {
        "markdown": str(out / "report.md"),
        "json": str(out / "report.json"),
        "pdf": str(out / "report.pdf"),
    }


def _render_pdf(state: RunState, reqs: Mapping[str, Any], path: Path) -> None:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        Flowable,
        HRFlowable,
        Paragraph,
        SimpleDocTemplate,
        Table,
        TableStyle,
    )

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.65 * inch,
        leftMargin=0.65 * inch,
        topMargin=0.65 * inch,
        bottomMargin=0.65 * inch,
        title=f"PlacementGap report — {state.student_id}",
        author="PlacementGap",
    )
    base = getSampleStyleSheet()
    title = ParagraphStyle(
        "PGTitle",
        parent=base["Title"],
        fontName="Helvetica-Bold",
        fontSize=23,
        textColor=colors.HexColor("#143b2a"),
        alignment=TA_LEFT,
        spaceAfter=6,
    )
    subtitle = ParagraphStyle(
        "PGSubtitle",
        parent=base["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#587060"),
        spaceAfter=15,
    )
    heading = ParagraphStyle(
        "PGHeading",
        parent=base["Heading2"],
        fontSize=14,
        textColor=colors.HexColor("#1b4c34"),
        spaceBefore=12,
        spaceAfter=7,
    )
    body = ParagraphStyle(
        "PGBody",
        parent=base["BodyText"],
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#26352c"),
        spaceAfter=6,
    )
    small = ParagraphStyle(
        "PGSmall", parent=body, fontSize=7, leading=9, textColor=colors.HexColor("#526258")
    )
    story: list[Flowable] = [
        Paragraph("PlacementGap report", title),
        Paragraph(
            f"Student: {escape(state.student_id)} · JD source tier: {escape(state.discovery_tier)} · {state.weeks} weeks at {state.hours_per_week:g} hours/week",
            subtitle,
        ),
        HRFlowable(color=colors.HexColor("#8ccca3"), thickness=1),
        Paragraph("Executive summary", heading),
        Paragraph(
            f"{len(state.gaps)} skill requirements assessed; {sum(g.verdict != 'has' for g in state.gaps)} need additional work. The proposed schedule respects a total capacity of {state.weeks * state.hours_per_week:g} hours.",
            body,
        ),
    ]
    if state.degraded:
        story += [
            Paragraph("Reduced scope", heading),
            Paragraph(escape("; ".join(state.degraded_reasons)), body),
        ]
    story.append(Paragraph("Gap analysis", heading))
    rows: list[list[object]] = [
        [
            Paragraph("Requirement", small),
            Paragraph("Verdict", small),
            Paragraph("Level gap", small),
            Paragraph("Evidence references", small),
        ]
    ]
    for g in state.gaps:
        req = reqs.get(g.skill_id)
        skill_text = getattr(req, "skill_text", g.skill_id)
        refs = []
        if req is not None and getattr(req, "evidence", None):
            ev = req.evidence
            refs.append(f"JD {ev.char_span[0]}–{ev.char_span[1]}")
        refs.extend(
            f"{escape(e.source_doc_id)} {e.char_span[0]}–{e.char_span[1]}" for e in g.evidence
        )
        rows.append(
            [
                Paragraph(escape(str(skill_text)), small),
                Paragraph(escape(g.verdict), small),
                Paragraph(str(g.level_delta), small),
                Paragraph("; ".join(refs) or "No profile evidence", small),
            ]
        )
    table = Table(
        rows,
        colWidths=[2.0 * inch, 0.75 * inch, 0.7 * inch, 3.1 * inch],
        repeatRows=1,
        hAlign="LEFT",
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e7f3eb")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#183c29")),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#d5e1d8")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7faf8")]),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(table)
    story.append(Paragraph("Week-by-week plan", heading))
    for week in range(1, state.weeks + 1):
        items = [p for p in state.plan if p.week == week]
        if items:
            story.append(
                Paragraph(
                    f"Week {week}",
                    ParagraphStyle(
                        f"Week{week}",
                        parent=body,
                        fontName="Helvetica-Bold",
                        textColor=colors.HexColor("#23583b"),
                    ),
                )
            )
            for item in items:
                text = f"<b>{escape(item.skill_id.replace('_', ' '))}</b> · {item.hours:g}h · {escape(item.objective)}"
                if item.status == "deferred":
                    text += f" (deferred: {escape(item.deferred_reason or '')})"
                else:
                    text += " · Resources: " + ", ".join(
                        f'<link href="{escape(u)}" color="#27754a">{escape(u)}</link>'
                        for u in item.resources
                    )
                story.append(Paragraph(text, body))
    story.append(Paragraph("Provenance appendix", heading))
    for index, gap in enumerate(state.gaps, start=1):
        req = reqs.get(gap.skill_id)
        if req is not None and getattr(req, "evidence", None):
            ev = req.evidence
            story.append(
                Paragraph(
                    f"[{index}] Job description chars {ev.char_span[0]}–{ev.char_span[1]}: “{escape(ev.quote)}” (confidence {ev.extractor_confidence:.2f})",
                    small,
                )
            )
        for evidence in gap.evidence:
            story.append(
                Paragraph(
                    f"[{index}] {escape(evidence.source_doc_id)} chars {evidence.char_span[0]}–{evidence.char_span[1]}: “{escape(evidence.quote)}” (confidence {evidence.extractor_confidence:.2f})",
                    small,
                )
            )

    def footer(canvas: Any, document: Any) -> None:
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#d5e1d8"))
        canvas.line(0.65 * inch, 0.48 * inch, 7.85 * inch, 0.48 * inch)
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.HexColor("#728077"))
        canvas.drawString(
            0.65 * inch, 0.32 * inch, "PLACEMENTGAP · EVIDENCE-GROUNDED SKILL ANALYSIS"
        )
        canvas.drawRightString(7.85 * inch, 0.32 * inch, f"{document.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    path.write_bytes(buffer.getvalue())
