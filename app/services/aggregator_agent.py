import logging
from pydantic import BaseModel, Field, ValidationError, field_validator
from google.adk.agents import Agent
from app.services.aggregator import score_to_status


def create_aggregator_agent(input_vars: str, model_obj) -> Agent:
    """
    Creates the aggregator agent that combines the chunks from the parallel team.
    """
    aggregator_instruction = f"""Combine and aggregate all the extracted insights from the parallel review analysis chunks below:

{input_vars}

You must execute a 6-stage flow to synthesize the findings:
1. **Collect**: Gather all raw insights from all chunks.
2. **Deduplicate**: Merge highly similar or duplicate insights. If two insights are nearly identical, group them, increment the frequency count, and choose the most representative quote as the example quote.
3. **Resolve Conflicts**: If insights on the same topic directly contradict each other (e.g., 'good battery' vs 'bad battery'), merge them into a single 'Mixed Feedback' insight. Sum their frequencies, average their confidences, and provide a quote that highlights the mixed consensus.
4. **Rank**: Group the unique insights. (Note: A final numerical score based on frequency, confidence, and category weights will be calculated automatically by the system).
5. **Quality Filter**: Keep all valid product feedback, positive reviews, issues, and features. Do not filter out insights unless they are completely blank, unrelated to the product, or gibberish.
6. **Format**: Output the final list of insights as a valid JSON array of objects conforming to this schema (leave score and status out, as the backend calculates them):
[
  {
    "insight": "Description of the insight",
    "confidence": 0.9,
    "frequency": 3,
    "example_quote": "Representative customer quote",
    "category": "quality"
  }
]

Important: Your response must be ONLY a valid JSON array and nothing else. No markdown wrappers like ```json or trailing text.
"""

    aggregator_agent = Agent(
        name="AggregatorAgent",
        model=model_obj,
        instruction=aggregator_instruction,
        output_key="executive_summary",
    )

    return aggregator_agent

logger = logging.getLogger(__name__)

VALID_CATEGORIES = {"quality", "support", "price", "usability", "other"}

# Defined here so Python can handle the math reliably
CATEGORY_WEIGHTS = {
    "quality": 1.5,
    "support": 1.2,
    "price": 1.0,
    "usability": 1.3,
    "other": 1.0
}

class InsightSchema(BaseModel):
    """
    Schema used to validate and sanitize the LLM output.
    """
    insight: str = Field(..., min_length=1)
    confidence: float = Field(..., ge=0.0, le=1.0)
    frequency: int = Field(..., gt=0)
    example_quote: str
    category: str
    
    # Populated dynamically via Python post-processing
    score: float | None = None
    status: str | None = None

    @field_validator("category")
    @classmethod
    def validate_and_lower_category(cls, v: str) -> str:
        """Enforces case-insensitivity and checks valid categories natively in Pydantic."""
        lowered = v.lower()
        if lowered not in VALID_CATEGORIES:
            raise ValueError(f"Category must be one of {VALID_CATEGORIES}")
        return lowered


def validate_insights(data: list) -> list:
    """
    Validates the JSON produced by the aggregator LLM, normalizes categories,
    and deterministically calculates scores in Python.
    """
    validated = []

    for index, item in enumerate(data):
        try:
            # 1. Validate basic schema and normalize category casing
            insight_obj = InsightSchema(**item)
            
            # 2. Safely calculate the mathematical score in Python
            weight = CATEGORY_WEIGHTS.get(insight_obj.category, 1.0)
            insight_obj.score = round(insight_obj.frequency * insight_obj.confidence * weight, 2)
            
            # 3. Assign your pipeline status
            insight_obj.status = score_to_status(insight_obj.score)

            validated.append(insight_obj.model_dump())

        except (ValidationError, ValueError) as e:
            logger.warning(
                f"Insight {index} failed validation: {e}"
            )

    logger.info(
        f"Validation Complete | "
        f"Accepted={len(validated)} | "
        f"Rejected={len(data)-len(validated)}"
    )

    return validated