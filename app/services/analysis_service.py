from google.adk.agents import SequentialAgent
from google.adk.runners import InMemoryRunner
from google.genai import types
from app.core.llm import model_obj, parallel_model_obj
from app.services.parallel_agent import create_parallel_team
from app.services.aggregator_agent import create_aggregator_agent
from app.schemas.insights import InsightsList
from logger import logger
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
                logger.info(
                    f"🔄 [Agent Event] Author: {author} | Node Path: {node_path}"
                )
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text:
                            snippet = part.text.strip().replace("\n", " ")
                            if len(snippet) > 100:
                                snippet = snippet[:100] + "..."
                            logger.info(f"   ├─ Output Text: {snippet}")
                if event.output is not None:
                    logger.info(f"   ├─ Output Data: {event.output}")

            if event.is_final_response() and author == "AggregatorAgent":
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text:
                            response_text += part.text
                if event.output is not None:
                    parsed_data = event.output

        # Enforce Pydantic parsing if ADK did not natively convert the string to the schema
        if parsed_data is None and response_text:
            try:
                # Strip Markdown code block if present
                clean_data = re.sub(
                    r"```(?:json)?\n(.*?)\n```", r"\1", response_text, flags=re.DOTALL
                ).strip()
                parsed_data = InsightsList.model_validate_json(clean_data)
            except Exception as e:
                logger.error(f"❌ Failed to parse JSON to Pydantic model: {e}")
                return response_text

        if parsed_data is not None:
            # We now have a guaranteed Pydantic InsightsList object
            for item in parsed_data.insights:
                try:
                    cat = str(item.category).lower().strip()
                    weight = category_weights.get(cat, 1.0)
                    item.score = round(item.frequency * item.confidence * weight, 2)
                except Exception:
                    pass

            return parsed_data

        return response_text

    except Exception as e:
        logger.error(f"❌ Error communicating with model provider: {e}")
        raise e
