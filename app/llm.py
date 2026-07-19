import os
import asyncio
from dotenv import load_dotenv
from google.adk.models import Gemini
from google.genai import types
from logger import logger

load_dotenv(override=True)

# Safety check for GEMINI_API_KEY
gemini_key = os.getenv("GEMINI_API_KEY")
if not gemini_key or gemini_key == "your_gemini_api_key_here":
    logger.warning(
        "⚠️ GEMINI_API_KEY is not configured in your environment or .env file."
    )

# Concurrency limit to prevent rate limits
CONCURRENCY_LIMIT = int(os.getenv("LOCAL_CONCURRENCY_LIMIT", "4"))
concurrency_semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)

_original_generate_content_async = Gemini.generate_content_async


async def _semaphore_generate_content_async(self, *args, **kwargs):
    async with concurrency_semaphore:
        async for response in _original_generate_content_async(self, *args, **kwargs):
            yield response


Gemini.generate_content_async = _semaphore_generate_content_async

# Model Configuration (Gemini 2.0 Flash)
GEMINI_MODEL_NAME = "gemini-3.1-flash-lite"

# Generation configuration for consistent responses
GENERATION_CONFIG = types.GenerateContentConfig(
    temperature=float(os.getenv("MODEL_TEMPERATURE", "0.0")),
    seed=int(os.getenv("MODEL_SEED", "42")),
    top_p=float(os.getenv("MODEL_TOP_P", "1.0")),
    max_output_tokens=int(os.getenv("MODEL_MAX_TOKENS", "8192")),
)

# ParallelModel Configuration
PARALLEL_GENERATION_CONFIG = types.GenerateContentConfig(
    temperature=float(os.getenv("MODEL_TEMPERATURE", "0.0")),
    seed=int(os.getenv("MODEL_SEED", "42")),
    top_p=float(os.getenv("MODEL_TOP_P", "1.0")),
    max_output_tokens=int(os.getenv("PARALLEL_MODEL_MAX_TOKENS", "4096")),
)

# Instantiate model objects
model_obj = Gemini(
    model=GEMINI_MODEL_NAME,
)
parallel_model_obj = Gemini(
    model=GEMINI_MODEL_NAME,
)

logger.info(f"✅ Aggregator Model: {GEMINI_MODEL_NAME}")
logger.info(f"✅ Parallel Model: {GEMINI_MODEL_NAME}")
