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

import re
import time

request_counter = 0
batch_lock = asyncio.Lock()


async def _semaphore_generate_content_async(self, *args, **kwargs):
    global request_counter
    max_retries = 5

    for attempt in range(max_retries):
        try:
            # 1. Enforce Batching (3 requests per minute) before semaphore
            async with batch_lock:
                request_counter += 1
                if request_counter > 4:
                    print(
                        f"\n⏳ [Rate Limit Manager] 4 requests processed. Initiating 60-second cooldown..."
                    )
                    for remaining in range(60, 0, -10):
                        print(f"   ⏱️  {remaining} seconds remaining...")
                        await asyncio.sleep(10)
                    print(
                        f"✅ [Rate Limit Manager] Cooldown complete. Resuming next batch...\n"
                    )
                    request_counter = 1

            # 2. Enforce Concurrency limit
            async with concurrency_semaphore:
                # Add a small 2s delay between starting requests to spread out the 30k TPM limit within the batch
                await asyncio.sleep(2)

                agen = _original_generate_content_async(self, *args, **kwargs)
                async for response in agen:
                    yield response
                return  # Success, exit the retry loop

        except litellm.exceptions.RateLimitError as e:
            if attempt == max_retries - 1:
                raise e

            # Extract the wait time from Groq's error message (e.g. "try again in 2.826s")
            msg = str(e)
            match = re.search(r"Please try again in ([0-9.]+)s", msg)
            if match:
                wait_time = float(match.group(1)) + 0.5
            else:
                wait_time = (2**attempt) + 1  # Fallback to exponential backoff

            print(
                f"⚠️ Rate limit hit. Waiting {wait_time:.2f}s before retry {attempt + 1}/{max_retries}..."
            )
            await asyncio.sleep(wait_time)


LiteLlm.generate_content_async = _semaphore_generate_content_async

# Configuration parameters for Groq models
LOCAL_MODEL_NAME = os.getenv(
    "LOCAL_MODEL_NAME", "groq/meta-llama/llama-4-scout-17b-16e-instruct"
)
LOCAL_PARALLEL_MODEL_NAME = os.getenv(
    "LOCAL_PARALLEL_MODEL_NAME", "groq/meta-llama/llama-4-scout-17b-16e-instruct"
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
    model=LOCAL_MODEL_NAME,
    **GENERATION_CONFIG,
)
parallel_model_obj = LiteLlm(
    model=LOCAL_PARALLEL_MODEL_NAME,
    **PARALLEL_GENERATION_CONFIG,
)

print(f"✅ Aggregator Model: {LOCAL_MODEL_NAME}")
print(f"✅ Parallel Sub-agents Model: {LOCAL_PARALLEL_MODEL_NAME}")
