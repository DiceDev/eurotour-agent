from __future__ import annotations

from collections import Counter

from .models import Recommendation, ResearchRun
from .planner import rank_candidate_trips


def render_markdown_report(research_run: ResearchRun) -> str:
    recommendations = rank_candidate_trips(
        calendar_windows=research_run.calendar_windows,
        candidate_trips=research_run.candidate_trips,
        currency_rates=research_run.currency_rates,
        trip_history=research_run.trip_history,
    )
    lines = [
        "# EuroTour Agent Report",
        "",
        f"- Generated: {research_run.generated_at.isoformat()}",
        f"- Mode: {research_run.mode}",
        f"- Watchlist: `{research_run.watchlist_path}`",
        "",
    ]

    if research_run.calendar_windows:
        lines.extend(["## Calendar Windows", ""])
        for window in research_run.calendar_windows:
            label = f" ({window.label})" if window.label else ""
            lines.append(f"- {window.starts_at.isoformat()} to {window.ends_at.isoformat()}{label}")
        lines.append("")

    if not recommendations:
        lines.extend(["## Recommendations", ""])
        lines.extend(["No candidate trips were found.", ""])
        return "\n".join(lines)

    decision_counts = Counter(recommendation.decision.value for recommendation in recommendations)
    lines.extend(["## Run Summary", ""])
    lines.append(f"- Candidate trips: {len(recommendations)}")
    if research_run.trip_history is not None:
        lines.append(f"- Prior trips recorded: {len(research_run.trip_history.trips)}")
    lines.append(
        "- Decisions: "
        + ", ".join(f"{decision}={count}" for decision, count in sorted(decision_counts.items()))
    )
    complete = sum(1 for recommendation in recommendations if recommendation.estimate_complete)
    lines.append(f"- Complete estimates: {complete}/{len(recommendations)}")
    lines.append("")

    lines.extend(["## Recommendations", ""])

    for index, recommendation in enumerate(recommendations, start=1):
        lines.extend(_render_recommendation(index, recommendation))

    if research_run.source_notes:
        lines.extend(["## Source Notes", ""])
        for note in research_run.source_notes:
            lines.append(f"- {note}")
        lines.append("")

    return "\n".join(lines)


def _render_recommendation(index: int, recommendation: Recommendation) -> list[str]:
    lines = [
        f"### {index}. {recommendation.title}",
        "",
        f"- Trip: {recommendation.trip_name}",
        f"- Decision: {recommendation.decision.value}",
        f"- Score: {recommendation.score:.3f}",
    ]
    if recommendation.estimated_total_amount is not None:
        completeness = "complete" if recommendation.estimate_complete else "partial"
        lines.append(
            f"- Estimated tracked cost: {recommendation.estimated_total_amount:.2f} {recommendation.estimated_total_currency} ({completeness})"
        )
    if recommendation.missing_cost_categories:
        missing = ", ".join(category.value for category in recommendation.missing_cost_categories)
        lines.append(f"- Missing cost categories: {missing}")
    lines.extend(["", recommendation.summary, "", "Reasons:"])
    lines.extend(f"- {reason}" for reason in recommendation.reasons)
    if recommendation.cost_breakdown:
        lines.append("")
        lines.append("Cost breakdown:")
        for component in recommendation.cost_breakdown:
            amount = "unknown" if component.amount is None else f"{component.amount:.2f} {component.currency}"
            lines.append(f"- {component.category.value}: {component.label} - {amount}")
    if recommendation.risks:
        lines.append("")
        lines.append("Risks:")
        lines.extend(f"- {risk}" for risk in recommendation.risks)
    if recommendation.next_actions:
        lines.append("")
        lines.append("Next actions:")
        lines.extend(f"- {action}" for action in recommendation.next_actions)
    lines.append("")
    return lines
