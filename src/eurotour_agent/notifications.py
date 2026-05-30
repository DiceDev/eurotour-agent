from __future__ import annotations

from pathlib import Path


def render_notification_digest(summary: dict, monitoring_brief: str | None = None) -> str:
    top = summary.get("top_recommendation") or {}
    outputs = summary.get("outputs") or {}
    lines = [
        "# EuroTour Daily Digest",
        "",
        f"Generated: {summary.get('generated_at', 'unknown')}",
        "",
        "## Snapshot",
        "",
        f"- Candidate trips: {summary.get('candidate_trips', 0)}",
        f"- Recommendations: {summary.get('recommendations', 0)}",
        f"- Price alerts: {summary.get('price_alerts', 0)}",
        "",
    ]

    lines.extend(["## Top Recommendation", ""])
    if top:
        lines.append(f"- {top.get('destination', 'Unknown')}: {top.get('decision', 'unknown')}")
        if top.get("score") is not None:
            lines.append(f"- Score: {float(top['score']):.3f}")
        if top.get("estimated_total_amount") is not None:
            lines.append(
                f"- Estimated tracked cost: {float(top['estimated_total_amount']):.2f} "
                f"{top.get('estimated_total_currency', '')}".rstrip()
            )
        reasons = top.get("reasons") or []
        if reasons:
            lines.append(f"- Main reason: {reasons[0]}")
    else:
        lines.append("- No top recommendation available.")
    lines.append("")

    lines.extend(["## Files", ""])
    for label in ["monitoring_brief", "report", "recommendations", "price_alerts", "research_run"]:
        if outputs.get(label):
            lines.append(f"- {label}: `{outputs[label]}`")
    lines.append("")

    if monitoring_brief:
        excerpt = _monitoring_excerpt(monitoring_brief)
        if excerpt:
            lines.extend(["## Brief Excerpt", "", *excerpt, ""])

    lines.extend(
        [
            "## Guardrails",
            "",
            "- Verify fares, rooms, tickets, and calendar availability on primary sources before booking.",
            "- This digest is advisory only; no purchase or message was sent automatically.",
            "",
        ]
    )
    return "\n".join(lines)


def render_notification_digest_from_files(summary_path: Path, monitoring_brief_path: Path | None = None) -> str:
    import json

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    monitoring_brief = (
        monitoring_brief_path.read_text(encoding="utf-8")
        if monitoring_brief_path is not None and monitoring_brief_path.exists()
        else None
    )
    return render_notification_digest(summary, monitoring_brief=monitoring_brief)


def _monitoring_excerpt(monitoring_brief: str) -> list[str]:
    wanted_headings = {"## Price Alerts", "## Next Actions"}
    lines = monitoring_brief.splitlines()
    excerpt: list[str] = []
    capture = False
    for line in lines:
        if line.startswith("## "):
            capture = line in wanted_headings
            if capture:
                excerpt.append(line)
            continue
        if capture:
            if line.startswith("# "):
                capture = False
                continue
            excerpt.append(line)
    return [line for line in excerpt if line.strip()][:12]
