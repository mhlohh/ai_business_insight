import os
from google.adk.agents import Agent, ParallelAgent
from app.services.chunker import chunk_reviews


def create_parallel_team(
    chunks: list[list[str]], parallel_model_obj
) -> tuple[ParallelAgent, str]:
    # Creates a ParallelAgent team based on chunks and returns it along with the aggregator input vars.

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
