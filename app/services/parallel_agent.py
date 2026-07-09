from google.adk.agents import Agent, ParallelAgent
from app.schemas.insights import InsightsList

def create_parallel_team(
    chunks: list[list[str]], parallel_model_obj
) -> tuple[ParallelAgent, str]:
    sub_agents = []
    input_vars = ""

    for i, chunk in enumerate(chunks):
        chunk_text = "\n".join(chunk)
        sub_agent = Agent(
            name=f"ReviewResearcher_{i}",
            model=parallel_model_obj,
            instruction=f"""Analyze the following product reviews, extract key business-relevant insights, issues, or features, and output a list of distinct insights.

CRITICAL INSTRUCTION: You MUST output ONLY raw, valid JSON matching the requested schema. DO NOT output any reasoning. DO NOT use `<think>` tags.

Reviews:
{chunk_text}""",
            output_key=f"insights_{i}",
            output_schema=InsightsList,
        )
        sub_agents.append(sub_agent)

        # Build aggregator prompt input string
        input_vars += f"\n**Chunk {i} Insights:**\n{{insights_{i}}}\n"

    parallel_reviews_team = ParallelAgent(
        name="ParallelReviewsTeam", sub_agents=sub_agents
    )

    return parallel_reviews_team, input_vars
