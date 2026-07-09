import os
from google.adk.agents import Agent, ParallelAgent, SequentialAgent
from google.adk.runners import InMemoryRunner
from google.genai import types

# New imports based on reorganized files
from app.core.llm import model_obj, parallel_model_obj
from app.schemas.insights import InsightsList
from app.services.parallel_agent import create_parallel_team
from app.services.aggregator_agent import create_aggregator_agent

# Status thresholds and values for priority score bucketing
STATUS_THRESHOLD_HIGH = 8.0
STATUS_THRESHOLD_MEDIUM = 5.0

STATUS_WORKING_WELL = "Working well"
STATUS_WORTH_WATCHING = "Worth watching"
STATUS_NEEDS_ATTENTION = "Needs attention"


def score_to_status(score: float) -> str:
    """
    Buckets a priority score into a business-readable plain-language status.
    """
    if score >= STATUS_THRESHOLD_HIGH:
        return STATUS_NEEDS_ATTENTION
    elif score >= STATUS_THRESHOLD_MEDIUM:
        return STATUS_WORTH_WATCHING
    else:
        return STATUS_WORKING_WELL


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





async def setup():
    """
    Setup function mapping to main.py lifespan contract.
    """
    pass


async def ask(prompt: str) -> str | list:
    """
    Core function called by FastAPI `/ask` endpoint (renamed to `/analyze` usually).
    Dynamically constructs a parallel review processing pipeline, runs it,
    and returns the aggregated result.
    """
    chunks = chunk_reviews(prompt)

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

        response_text = ""
        final_insights_data = None

        async for event in runner.run_async(
            user_id="user",
            session_id=session.id,
            new_message=types.Content(
                role="user",
                parts=[types.Part(text="Run the product review aggregation pipeline.")],
            ),
        ):
            node_path = event.node_info.path if event.node_info else "unknown"
            author = event.author or "System"

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
                if event.output is not None:
                    if hasattr(event.output, "model_dump"):
                        final_insights_data = event.output.model_dump().get("insights", [])
                    elif hasattr(event.output, "dict"):
                        final_insights_data = event.output.dict().get("insights", [])
                    elif isinstance(event.output, dict):
                        final_insights_data = event.output.get("insights", [])
                    elif isinstance(event.output, list):
                        final_insights_data = event.output

                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text:
                            response_text += part.text

        data = final_insights_data

        # Fallback: if ADK did not auto-parse into event.output, parse the raw JSON text manually
        if data is None and response_text:
            try:
                import json
                
                def extract_json_object(text: str) -> str:
                    start = text.find('{')
                    if start == -1: return ""
                    brace_count = 0
                    in_string = False
                    escape = False
                    for i in range(start, len(text)):
                        char = text[i]
                        if escape:
                            escape = False
                            continue
                        if char == '\\':
                            escape = True
                            continue
                        if char == '"':
                            in_string = not in_string
                            continue
                        if not in_string:
                            if char == '{':
                                brace_count += 1
                            elif char == '}':
                                brace_count -= 1
                                if brace_count == 0:
                                    return text[start:i+1]
                    return ""

                # Surgically extract the JSON object using brace counting
                clean_json_str = extract_json_object(response_text)
                if clean_json_str:
                    parsed_json = json.loads(clean_json_str)
                    data = parsed_json.get("insights", [])
                else:
                    print("⚠️ No JSON block found in response.")
            except Exception as e:
                print(f"⚠️ Failed to parse raw JSON string: {e}")

        if data is None:
            raise ValueError("Pydantic structured output not found. The model failed to conform to the required JSON schema.")

        if data is not None and isinstance(data, list):
            category_weights = {
                "quality": 1.5,
                "support": 1.2,
                "usability": 1.3,
                "price": 1.0,
            }
            for item in data:
                if isinstance(item, dict):
                    try:
                        freq = float(item.get("frequency", item.get("count", 1)))
                        conf = float(
                            item.get("confidence", item.get("confidence_level", 0.8))
                        )
                        cat = str(item.get("category", "other")).lower().strip()
                        weight = category_weights.get(cat, 1.0)
                        calculated_score = freq * conf * weight
                        item["score"] = round(calculated_score, 2)

                        if "example_quote" not in item and "quote" in item:
                            item["example_quote"] = item["quote"]
                        if "confidence" not in item:
                            item["confidence"] = conf
                        if "frequency" not in item:
                            item["frequency"] = freq
                    except (ValueError, TypeError):
                        pass

                    try:
                        item["status"] = score_to_status(float(item["score"]))
                    except (ValueError, TypeError):
                        item["status"] = STATUS_NEEDS_ATTENTION
            return data

        raise ValueError("Model output was not a valid list.")

    except Exception as e:
        print(f"❌ Error communicating with LLM provider (Groq): {e}")
        print(
            "👉 Please ensure that your GROQ_API_KEY is correctly set in your .env file."
        )
        raise e
