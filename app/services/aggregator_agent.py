from google.adk.agents import Agent


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
4. **Score/Rank**: Calculate a score for each unique insight using the formula:
   score = frequency * confidence * category_weight
   Use the following category weights:
   - quality: 1.5
   - support: 1.2
   - price: 1.0
   - usability: 1.3
   - other: 1.0
   (Assume confidence is the average confidence of the merged insights, and frequency is the number of times it was mentioned or merged.)
5. **Quality Filter**: Keep all valid product feedback, positive reviews, issues, and features. Do not filter out insights unless they are completely blank, unrelated to the product, or gibberish.
6. **Format**: Output the final ranked list of insights as a valid JSON array of objects conforming to this schema:
[
  {{
    "insight": "Description of the insight",
    "score": 4.5,
    "confidence": 0.9,
    "status": "Working well",
    "frequency": 3,
    "example_quote": "Representative customer quote",
    "category": "quality"
  }}
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
