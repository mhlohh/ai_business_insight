import os
import json
from google.adk.agents import Agent, ParallelAgent, SequentialAgent
from google.adk.runners import InMemoryRunner
from google.genai import types

# New imports based on reorganized files
from app.core.llm import model_obj, parallel_model_obj
from app.schemas.insights import InsightsList
from app.services.parallel_agent import create_parallel_team
from app.services.aggregator_agent import create_aggregator_agent
from app.services.chunker import chunkers


# Status thresholds and values for priority score bucketing
STATUS_THRESHOLD_HIGH = 8.0
STATUS_THRESHOLD_MEDIUM = 5.0

STATUS_WORKING_WELL = "Working well"
STATUS_WORTH_WATCHING = "Worth watching"
STATUS_NEEDS_ATTENTION = "Needs attention"


def score_to_status(score: float) -> str:
    """Buckets a priority score into a business-readable plain-language status."""
    if score >= STATUS_THRESHOLD_HIGH:
        return STATUS_NEEDS_ATTENTION
    elif score >= STATUS_THRESHOLD_MEDIUM:
        return STATUS_WORTH_WATCHING
    else:
        return STATUS_WORKING_WELL


def _log_agent_event(event, author: str, node_path: str):
    """Logs the agent event in a clean, descriptive format."""
    # ANSI color codes
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    MAGENTA = "\033[95m"
    YELLOW = "\033[93m"
    GREEN = "\033[92m"
    RED = "\033[91m"
    RESET = "\033[0m"

    if author == "System":
        print(f"{BLUE}[System]{RESET} Routing or pipeline event. Path: {node_path}")
    elif "ReviewResearcher" in author:
        print(
            f"{CYAN}[Parallel Analysis]{RESET} {author} successfully processed its review chunk."
        )
    elif "AggregatorAgent" in author:
        print(
            f"{MAGENTA}[Pipeline Synthesis]{RESET} {author} successfully aggregated all sub-agent findings."
        )
    else:
        print(
            f"{YELLOW}[Agent Operation]{RESET} {author} completed task on node: {node_path}"
        )

    if event.content and event.content.parts:
        for part in event.content.parts:
            if part.text:
                print(f"   ├─ Generated {len(part.text)} characters of text.")

    if event.output is not None:
        try:
            items_count = len(_extract_output_data(event.output) or [])
            if items_count > 0:
                print(
                    f"   ├─ {GREEN}Extracted {items_count} structured insights.{RESET}"
                )
            else:
                print(
                    f"   ├─ {RED}Structured output parsed, but no insights list found.{RESET}"
                )
        except Exception:
            print(f"   ├─ {GREEN}Structured output parsed successfully.{RESET}")


def _extract_output_data(output) -> list | None:
    """Attempts to extract the insights list from various potential ADK output formats."""
    if output is None:
        return None
    if hasattr(output, "model_dump"):
        return output.model_dump().get("insights", [])
    elif hasattr(output, "dict"):
        return output.dict().get("insights", [])
    elif isinstance(output, dict):
        return output.get("insights", [])
    elif isinstance(output, list):
        return output
    return None


def _extract_json_fallback(response_text: str) -> list | None:
    """Manually extracts JSON from raw text using brace counting if strict parsing failed."""
    if not response_text:
        return None

    start = response_text.find("{")
    if start == -1:
        return None

    brace_count = 0
    in_string = False
    escape = False

    for i in range(start, len(response_text)):
        char = response_text[i]
        if escape:
            escape = False
            continue
        if char == "\\":
            escape = True
            continue
        if char == '"':
            in_string = not in_string
            continue
        if not in_string:
            if char == "{":
                brace_count += 1
            elif char == "}":
                brace_count -= 1
                if brace_count == 0:
                    clean_json_str = response_text[start : i + 1]
                    try:
                        parsed = json.loads(clean_json_str)
                        return parsed.get("insights", [])
                    except json.JSONDecodeError:
                        return None
    return None


def _enrich_insights_data(data: list) -> list:
    """Calculates scores, standardizes fields, and assigns business statuses to insights."""
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
                conf = float(item.get("confidence", item.get("confidence_level", 0.8)))
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

                item["status"] = score_to_status(float(item["score"]))

            except (ValueError, TypeError):
                item["status"] = STATUS_NEEDS_ATTENTION

    return data


async def setup():
    """Setup function mapping to main.py lifespan contract."""
    pass


async def ask(prompt: str) -> str | list:
    """
    Core function called by FastAPI `/ask` endpoint (renamed to `/analyze` usually).
    Dynamically constructs a parallel review processing pipeline, runs it,
    and returns the aggregated result.
    """
    chunks = chunkers(prompt)

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
                _log_agent_event(event, author, node_path)

            if event.is_final_response():
                if event.output is not None:
                    final_insights_data = _extract_output_data(event.output)

                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text:
                            response_text += part.text

        data = final_insights_data

        # Fallback manual extraction if ADK failed to auto-parse
        if data is None and response_text:
            data = _extract_json_fallback(response_text)
            if data is None:
                print("⚠️ Failed to parse raw JSON string or no JSON block found.")

        if data is None:
            raise ValueError(
                "Pydantic structured output not found. The model failed to conform to the required JSON schema."
            )

        if isinstance(data, list):
            return _enrich_insights_data(data)

        raise ValueError("Model output was not a valid list.")

    except Exception as e:
        error_msg = str(e)
        RED = "\033[91m"
        RESET = "\033[0m"

        # Save the raw error to a log file for debugging
        try:
            import datetime

            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open("llm_error.log", "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] LLM Exception: {error_msg}\n")
        except Exception:
            pass

        if (
            "RateLimitError" in error_msg
            or "rate limit" in error_msg.lower()
            or "tokens per minute" in error_msg.lower()
        ):
            print(
                f"{RED}❌ [RATE LIMIT EXCEEDED] Groq API tokens-per-minute (TPM) limit reached.{RESET}"
            )
            print("👉 The parallel chunk queue processed too many tokens too fast.")
            print(
                "👉 Fix: Lower 'LOCAL_CONCURRENCY_LIMIT' or 'MAX_REVIEWS_TO_ANALYZE' in your .env file."
            )
            print("📝 The full error details have been saved to 'llm_error.log'.")
        else:
            print(
                f"{RED}❌ Error communicating with LLM provider (Groq):{RESET} {error_msg}"
            )
            print(
                "👉 Please ensure that your GROQ_API_KEY is correctly set in your .env file."
            )
            print("📝 The full error details have been saved to 'llm_error.log'.")

        raise e


async def ask_stream(prompt: str):
    """
    Core function that behaves like ask() but yields progress events.
    """
    chunks = chunkers(prompt)
    num_chunks = len(chunks)

    yield {
        "status": "init",
        "num_chunks": num_chunks,
        "message": "Initializing pipeline...",
    }

    parallel_reviews_team, input_vars = create_parallel_team(chunks, parallel_model_obj)
    aggregator_agent = create_aggregator_agent(input_vars, model_obj)

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
        chunks_processed = 0

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
                _log_agent_event(event, author, node_path)

                if "ReviewResearcher" in author:
                    chunks_processed += 1
                    yield {
                        "status": "processing",
                        "chunks_processed": chunks_processed,
                        "num_chunks": num_chunks,
                        "message": f"Processing chunk {chunks_processed}/{num_chunks}...",
                    }
                elif "AggregatorAgent" in author:
                    yield {
                        "status": "aggregating",
                        "chunks_processed": chunks_processed,
                        "num_chunks": num_chunks,
                        "message": "Aggregating insights...",
                    }

            if event.is_final_response():
                if event.output is not None:
                    final_insights_data = _extract_output_data(event.output)

                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text:
                            response_text += part.text

        data = final_insights_data

        if data is None and response_text:
            data = _extract_json_fallback(response_text)
            if data is None:
                print("⚠️ Failed to parse raw JSON string or no JSON block found.")

        if data is None:
            raise ValueError(
                "Pydantic structured output not found. The model failed to conform to the required JSON schema."
            )

        if isinstance(data, list):
            enriched = _enrich_insights_data(data)
            yield {"status": "completed", "result": enriched}
            return

        raise ValueError("Model output was not a valid list.")

    except Exception as e:
        error_msg = str(e)
        RED = "\033[91m"
        RESET = "\033[0m"

        try:
            import datetime

            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open("llm_error.log", "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] LLM Exception: {error_msg}\n")
        except Exception:
            pass

        if (
            "RateLimitError" in error_msg
            or "rate limit" in error_msg.lower()
            or "tokens per minute" in error_msg.lower()
        ):
            print(
                f"{RED}❌ [RATE LIMIT EXCEEDED] Groq API tokens-per-minute (TPM) limit reached.{RESET}"
            )
            yield {"status": "error", "message": "Rate limit exceeded"}
        else:
            print(f"{RED}❌ Error communicating with LLM provider:{RESET} {error_msg}")
            yield {"status": "error", "message": error_msg}

        raise e
