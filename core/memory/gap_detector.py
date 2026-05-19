import logging
from sqlalchemy.ext.asyncio import AsyncSession

from core.memory.store import count_memories_by_category
from llm.router import llm_router, LLMError
from llm.prompts import GAP_ANALYSIS_PROMPT

logger = logging.getLogger(__name__)

REQUIRED_CATEGORIES: dict[str, dict] = {
    "leadership":            {"minimum": 3, "weight": "high"},
    "conflict_resolution":   {"minimum": 2, "weight": "high"},
    "failure_learning":      {"minimum": 2, "weight": "high"},
    "technical_achievement": {"minimum": 3, "weight": "high"},
    "collaboration":         {"minimum": 2, "weight": "medium"},
    "ambiguity_handling":    {"minimum": 2, "weight": "medium"},
    "initiative":            {"minimum": 2, "weight": "medium"},
    "system_design":         {"minimum": 1, "weight": "high"},
    "debugging":             {"minimum": 2, "weight": "medium"},
    "tech_decisions":        {"minimum": 2, "weight": "high"},
    "career_goal":           {"minimum": 1, "weight": "medium"},
    "value":                 {"minimum": 1, "weight": "low"},
    "strength":              {"minimum": 2, "weight": "medium"},
}

WEIGHT_ORDER = {"high": 0, "medium": 1, "low": 2}


async def detect_gaps(db: AsyncSession) -> list[dict]:
    counts = await count_memories_by_category(db)
    gaps = []

    for category, config in REQUIRED_CATEGORIES.items():
        have = counts.get(category, 0)
        need = config["minimum"]
        if have < need:
            gaps.append({
                "category": category,
                "have": have,
                "need": need,
                "deficit": need - have,
                "priority": config["weight"],
                "suggested_questions": [],
            })

    gaps.sort(key=lambda g: (WEIGHT_ORDER.get(g["priority"], 99), -g["deficit"]))

    # Generate fill questions for high-priority gaps (LLM call)
    high_gaps = [g for g in gaps if g["priority"] == "high"]
    if high_gaps:
        gap_list = "\n".join(
            f"- {g['category']}: have {g['have']}, need {g['need']}"
            for g in high_gaps
        )
        memory_counts = "\n".join(
            f"  {cat}: {cnt}" for cat, cnt in counts.items()
        ) or "  (no memories yet)"

        try:
            result = await llm_router.call(
                "gap_analysis",
                GAP_ANALYSIS_PROMPT.format(
                    gap_categories=gap_list,
                    memory_counts=memory_counts,
                ),
                max_tokens=2000,
            )
            parsed = llm_router.parse_json_response(result)
            for item in parsed.get("gap_questions", []):
                cat = item.get("category")
                question = item.get("question")
                for g in gaps:
                    if g["category"] == cat and not g["suggested_questions"]:
                        g["suggested_questions"] = [question]
                        break
        except (LLMError, ValueError) as e:
            logger.warning(f"Gap analysis LLM failed: {e}")

    return gaps


async def get_gap_summary(db: AsyncSession) -> str:
    gaps = await detect_gaps(db)
    if not gaps:
        return "[green]All required memory categories are covered![/green]"

    lines = [
        f"[bold]Found {len(gaps)} memory gaps:[/bold]\n"
    ]
    for g in gaps:
        priority_color = {"high": "red", "medium": "yellow", "low": "cyan"}.get(g["priority"], "white")
        bar = "█" * g["have"] + "░" * (g["need"] - g["have"])
        lines.append(
            f"  [{priority_color}]{g['category']:25s}[/{priority_color}] "
            f"{bar} {g['have']}/{g['need']}  [{g['priority'].upper()}]"
        )
        if g.get("suggested_questions"):
            lines.append(f"    → {g['suggested_questions'][0]}")

    return "\n".join(lines)
