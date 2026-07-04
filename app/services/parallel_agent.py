import os
from google.adk.agents import Agent, ParallelAgent


def chunk_reviews(prompt: str) -> list[list[str]]:
    """
    Helper to chunk a large block of reviews (each review on a separate line)
    into smaller sub-lists of reviews.
    """
    lines = [line.strip() for line in prompt.split("\n") if line.strip()]
    if not lines:
        return [["No reviews provided."]]

    # Cap total reviews to analyze for performance and context limits of local models
    max_reviews = int(os.getenv("MAX_REVIEWS_TO_ANALYZE", "100"))
    lines = lines[:max_reviews]

    # Dynamically select a chunk size based on input size
    if len(lines) < 10:
        chunk_size = 3
    elif len(lines) < 100:
        chunk_size = 10
    else:
        chunk_size = 20  # 5 chunks of 20 reviews for max 100

    chunks = []
    for i in range(0, len(lines), chunk_size):
        chunks.append(lines[i : i + chunk_size])
    return chunks


def create_parallel_team(
    chunks: list[list[str]], parallel_model_obj
) -> tuple[ParallelAgent, str]:
    """
    Creates a ParallelAgent team based on chunks and returns it along with the aggregator input vars.
    """
    sub_agents = []
    input_vars = ""

    for i, chunk in enumerate(chunks):
        chunk_text = "\n".join(chunk)
        sub_agent = Agent(
            name=f"ReviewResearcher_{i}",
            model=parallel_model_obj,
            instruction=f"""Analyze the following product reviews, extract key business-relevant insights, issues, or features, and output a list of distinct insights.
For each insight, include:
- The insight description
- A representative quote
- A confidence level (between 0.0 and 1.0)
- The category of the insight (e.g., quality, support, price, usability, etc.)

Reviews:
{chunk_text}""",
            output_key=f"insights_{i}",
        )
        sub_agents.append(sub_agent)

        # Build aggregator prompt input string
        input_vars += f"\n**Chunk {i} Insights:**\n{{insights_{i}}}\n"

    parallel_reviews_team = ParallelAgent(
        name="ParallelReviewsTeam", sub_agents=sub_agents
    )

    return parallel_reviews_team, input_vars
