from google.adk.agents import Agent
from app.schemas.insights import InsightsList


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
4. **Quality Filter**: Keep all valid product feedback, positive reviews, issues, and features. Do not filter out insights unless they are completely blank, unrelated to the product, or gibberish.
"""

    aggregator_agent = Agent(
        name="AggregatorAgent",
        model=model_obj,
        instruction=aggregator_instruction,
        output_key="executive_summary",
        output_schema=InsightsList,
    )
    return aggregator_agent
