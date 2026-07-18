from google.adk.agents import SequentialAgent
from google.adk.runners import InMemoryRunner
from google.genai import types
from app.services.llm_config import model_obj, parallel_model_obj
from app.services.parallel_agent import create_parallel_team
from app.services.aggregator_agent import create_aggregator_agent
from app.models import InsightsList
import json
import re


category_weights = {
    "quality": 1.5,
    "support": 1.2,
    "usability": 1.3,
    "price": 1.0,
}


async def setup():
    """
    Setup function mapping to main.py lifespan contract.
    No global runner is built here as the pipeline is dynamically constructed
    per request based on the size of the reviews list.
    """
    pass


async def ask(chunks: list[list[str]]) -> str | list:
    """
    Core function called by FastAPI `/ask` endpoint.
    Dynamically constructs a parallel review processing pipeline, runs it,
    and returns the aggregated result.
    """

    # 1. Create Parallel Sub-agents for each chunk using the parallel model object
    parallel_reviews_team, input_vars = create_parallel_team(chunks, parallel_model_obj)

    # 2. Formulate Aggregator Prompt using the output keys from sub-agents
    aggregator_agent = create_aggregator_agent(input_vars, model_obj)

    # 3. Create the root Sequential Agent and InMemoryRunner
    root_agent = SequentialAgent(
        name="ReviewsAnalysisSystem",
        sub_agents=[parallel_reviews_team, aggregator_agent],
        output_schema=InsightsList,
    )

    runner = InMemoryRunner(agent=root_agent)

    try:
        session = await runner.session_service.create_session(
            app_name=runner.app_name,
            user_id="user",
        )

        parsed_data = None
        response_text = ""
        async for event in runner.run_async(
            user_id="user",
            session_id=session.id,
            new_message=types.Content(
                role="user",
                parts=[types.Part(text="Run the product review aggregation pipeline.")],
            ),
        ):
            # Print execution logs for parallel agents, aggregator, and root agent
            node_path = event.node_info.path if event.node_info else "unknown"
            author = event.author or "System"

            # Print intermediate agent trace if not partial/stream chunks
            if not event.partial:
                print(f"🔄 [Agent Event] Author: {author} | Node Path: {node_path}")
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text:
                            snippet = part.text.strip().replace("\n", " ")
                            if len(snippet) > 100:
                                snippet = snippet[:100] + "..."
                            print(f"   ├─ Output Text: {snippet}")
                if event.output is not None:
                    print(f"   ├─ Output Data: {event.output}")

            if event.is_final_response() and author == "AggregatorAgent":
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text:
                            response_text += part.text
                if event.output is not None:
                    parsed_data = event.output

        # Since ADK parses the output_schema automatically, event.output is our parsed InsightsList
        if parsed_data is not None:
            # We can process the Pydantic object directly
            insights = []
            if hasattr(parsed_data, "insights"):
                insights = parsed_data.insights
            elif isinstance(parsed_data, dict):
                insights = parsed_data.get("insights", [])

            for item in insights:
                # If it's a Pydantic object, we might want to update it, but usually it's better to just return the clean model
                # or we can update fields if they are dicts
                if isinstance(item, dict):
                    try:
                        freq = float(item.get("frequency", 1))
                        conf = float(item.get("confidence", 0.8))
                        cat = str(item.get("category", "other")).lower().strip()
                        weight = category_weights.get(cat, 1.0)
                        item["score"] = round(freq * conf * weight, 2)
                    except (ValueError, TypeError):
                        pass
                else:
                    # It's an AI_Insight Pydantic model
                    try:
                        freq = float(item.frequency)
                        conf = float(item.confidence)
                        cat = str(item.category).lower().strip()
                        weight = category_weights.get(cat, 1.0)
                        # We would set the score, but 'score' is not in the AI_Insight model
                        # For now, just return the Pydantic object directly, FastAPI handles serialization
                        pass
                    except Exception:
                        pass

            return parsed_data

        return response_text

    except Exception as e:
        print(f"❌ Error communicating with model provider: {e}")
        raise e
