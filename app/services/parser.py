import re
import json
from app.services.aggregator_agent import score_to_status


def parse_fallback_insights(text: str) -> list[dict]:
    insights = []
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    for line in lines:
        if line.lower().startswith(
            (
                "here is",
                "sure",
                "ok",
                "based on",
                "the analysis",
                "overall",
                "i analyzed",
            )
        ):
            continue

        cleaned = re.sub(r"^[\d\-\*\.\)\s\•]+", "", line).strip()
        if not cleaned or len(cleaned) < 15:
            continue

        score_match = re.search(
            r"(?:score|rating)[\s:]*([\d\.]+)", cleaned, re.IGNORECASE
        )
        score = 5.0
        if score_match:
            try:
                score = float(score_match.group(1))
            except ValueError:
                pass

        category_match = re.search(r"category[\s:]*([a-zA-Z]+)", cleaned, re.IGNORECASE)
        category = "Other"
        if category_match:
            category = category_match.group(1)

        status = score_to_status(score)

        cleaned_insight = re.sub(
            r"[\(\[\{][^\)\]\}]*(?:score|rating|category)[^\)\]\}]*[\)\]\}]",
            "",
            cleaned,
            flags=re.IGNORECASE,
        ).strip()
        cleaned_insight = re.sub(r"\s+", " ", cleaned_insight).strip()
        cleaned_insight = cleaned_insight.rstrip(",;:- ")

        if cleaned_insight:
            insights.append(
                {
                    "insight": cleaned_insight,
                    "score": score,
                    "status": status,
                    "frequency": 1,
                    "example_quote": "Extracted from text report.",
                    "category": category.lower(),
                }
            )

    if not insights and text.strip():
        insights.append(
            {
                "insight": (
                    text.strip()[:250] + "..."
                    if len(text.strip()) > 250
                    else text.strip()
                ),
                "score": 5.0,
                "status": "Worth watching",
                "frequency": 1,
                "example_quote": "Refer to raw output for details.",
                "category": "other",
            }
        )

    return insights


def extract_insights_json(text: str) -> list | None:
    """
    Robustly extracts the final JSON insights array from the model response text,
    skipping any echoed example templates or parsing artifacts.
    """
    blocks = []

    # 1. Try extracting from ```json blocks (in reverse order, processing last first)
    if "```json" in text:
        parts = text.split("```json")
        for part in reversed(parts[1:]):
            block = part.split("```")[0].strip()
            try:
                data = json.loads(block)
                if isinstance(data, list) and len(data) > 0:
                    if not (
                        len(data) == 1
                        and data[0].get("insight") == "Description of the insight"
                    ):
                        return data
                    else:
                        blocks.append(data)
            except Exception:
                pass

    # 2. Try extracting from generic ``` blocks (in reverse order)
    if "```" in text:
        parts = text.split("```")
        for i in reversed(range(1, len(parts), 2)):
            block = parts[i].strip()
            if block.lower().startswith("json"):
                block = block[4:].strip()
            try:
                data = json.loads(block)
                if isinstance(data, list) and len(data) > 0:
                    if not (
                        len(data) == 1
                        and data[0].get("insight") == "Description of the insight"
                    ):
                        return data
                    else:
                        blocks.append(data)
            except Exception:
                pass

    # 3. Try finding any [...] array block using bracket matching from the end
    start_positions = [m.start() for m in re.finditer(r"\[", text)]
    for start_idx in reversed(start_positions):
        bracket_count = 0
        end_idx = -1
        for i in range(start_idx, len(text)):
            if text[i] == "[":
                bracket_count += 1
            elif text[i] == "]":
                bracket_count -= 1
                if bracket_count == 0:
                    end_idx = i
                    break
        if end_idx != -1:
            candidate = text[start_idx : end_idx + 1]
            try:
                data = json.loads(candidate)
                if isinstance(data, list) and len(data) > 0:
                    if not (
                        len(data) == 1
                        and data[0].get("insight") == "Description of the insight"
                    ):
                        return data
                    else:
                        blocks.append(data)
            except Exception:
                pass

    if blocks:
        return blocks[0]
    return None
