from google.adk.agents import SequentialAgent
from google.adk.runners import InMemoryRunner
from google.genai import types
from app.services.llm_config import model_obj, parallel_model_obj
from app.services.parallel_agent import create_parallel_team
from app.services.aggregator_agent import create_aggregator_agent
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

            if event.is_final_response():
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text:
                            response_text += part.text
                if event.output is not None:
                    parsed_data = event.output

        # Post-process response to extract only the JSON array if available
       
        if parsed_data is None and response_text:
            try:
                # Remove markdown code blocks if any
                clean_data = re.sub(r'```(?:json)?\n(.*?)\n```', r'\1', response_text, flags=re.DOTALL).strip()
                parsed_data = json.loads(clean_data)
            except json.JSONDecodeError as e:
                print(f"❌ Failed to parse JSON from response: {e}")
                return response_text

        if parsed_data is not None:
            insights = parsed_data.get("insights", []) if isinstance(parsed_data, dict) else parsed_data
            if hasattr(parsed_data, "insights"): # Check if it's a Pydantic object
                insights = parsed_data.insights

            if isinstance(insights, list):
                for item in insights:
                    if isinstance(item, dict):
                        # Recalculate score programmatically
                        try:
                            freq = float(item.get("frequency", item.get("count", 1)))
                            conf = float(item.get("confidence", item.get("confidence_level", 0.8)))
                            cat = str(item.get("category", "other")).lower().strip()
                            weight = category_weights.get(cat, 1.0)
                            item["score"] = round(freq * conf * weight, 2)
                            # Normalize keys for frontend
                            if "example_quote" not in item and "quote" in item:
                                item["example_quote"] = item["quote"]
                            if "frequency" not in item:
                                item["frequency"] = freq
                        except (ValueError, TypeError):
                            pass

            if isinstance(parsed_data, dict):
                parsed_data["insights"] = insights
                return parsed_data
            elif isinstance(parsed_data, list):
                return {"insights": insights}
            else: # Return the parsed Pydantic ADK response directly
                return parsed_data
                
        return response_text

    except Exception as e:
        print(f"❌ Error communicating with local model provider: {e}")
        print(
            f"👉 Please ensure that your local LM Studio server is running and listening on {LMSTUDIO_API_BASE}"
        )
        raise e
