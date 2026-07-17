import os
import asyncio
import litellm
from dotenv import load_dotenv
from google.adk.models.lite_llm import LiteLlm

load_dotenv(override=True)

# Configure LiteLLM to automatically retry on rate limits
litellm.num_retries = 3
try:
    litellm.retry_policy = litellm.RetryPolicy(
        RateLimitErrorRetries=5, TimeoutErrorRetries=3
    )
except AttributeError:
    pass

# Concurrency limit to prevent Groq API rate limits (TPM)
CONCURRENCY_LIMIT = int(os.getenv("LOCAL_CONCURRENCY_LIMIT", "4"))
concurrency_semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)

_original_generate_content_async = LiteLlm.generate_content_async


async def _semaphore_generate_content_async(self, *args, **kwargs):
    async with concurrency_semaphore:
        async for response in _original_generate_content_async(self, *args, **kwargs):
            yield response


LiteLlm.generate_content_async = _semaphore_generate_content_async

# Configuration parameters for Groq models
GROQ_MODEL_NAME = os.getenv(
    "GROQ_MODEL_NAME", "groq/meta-llama/llama-4-scout-17b-16e-instruct"
)
GROQ_PARALLEL_MODEL_NAME = os.getenv(
    "GROQ_PARALLEL_MODEL_NAME", "groq/meta-llama/llama-4-scout-17b-16e-instruct"
)

# Generation configuration for consistent responses
GENERATION_CONFIG = {
    "temperature": float(os.getenv("MODEL_TEMPERATURE", "0.0")),
    "seed": int(os.getenv("MODEL_SEED", "42")),
    "top_p": float(os.getenv("MODEL_TOP_P", "1.0")),
    "max_tokens": int(os.getenv("MODEL_MAX_TOKENS", "8192")),
}

# ParallelModel Configuration
PARALLEL_GENERATION_CONFIG = {
    "temperature": float(os.getenv("MODEL_TEMPERATURE", "0.0")),
    "seed": int(os.getenv("MODEL_SEED", "42")),
    "top_p": float(os.getenv("MODEL_TOP_P", "1.0")),
    "max_tokens": int(os.getenv("PARALLEL_MODEL_MAX_TOKENS", "4096")),
}

# Instantiate model objects
model_obj = LiteLlm(
    model=GROQ_MODEL_NAME,
    **GENERATION_CONFIG,
)
parallel_model_obj = LiteLlm(
    model=GROQ_PARALLEL_MODEL_NAME,
    **PARALLEL_GENERATION_CONFIG,
)

print(f"✅ Aggregator Model: {GROQ_MODEL_NAME}")
print(f"✅ Parallel Model: {GROQ_PARALLEL_MODEL_NAME}")