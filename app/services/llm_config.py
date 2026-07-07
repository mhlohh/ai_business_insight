import os
import asyncio
from dotenv import load_dotenv
from google.adk.models.lite_llm import LiteLlm

load_dotenv(override=True)

# Configuration parameters for LM Studio / LiteLLM local models
LOCAL_MODEL_NAME = os.getenv("LOCAL_MODEL_NAME", "openai/google/gemma-4-e4b")
LOCAL_PARALLEL_MODEL_NAME = os.getenv(
    "LOCAL_PARALLEL_MODEL_NAME", "openai/google/gemma-4-e4b"
)
LMSTUDIO_API_BASE = os.getenv("LMSTUDIO_API_BASE", "http://localhost:1234/v1")
LMSTUDIO_API_KEY = os.getenv("LMSTUDIO_API_KEY", "lm-studio")

# LiteLLM/LM Studio configuration
os.environ["OPENAI_API_BASE"] = LMSTUDIO_API_BASE
os.environ["OPENAI_API_KEY"] = LMSTUDIO_API_KEY

# Concurrency limit for local model provider to prevent LM Studio compute/OOM errors under concurrent load
CONCURRENCY_LIMIT = int(os.getenv("LOCAL_CONCURRENCY_LIMIT", "4"))
concurrency_semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)

# Monkeypatch LiteLlm.generate_content_async to enforce the concurrency limit
_original_generate_content_async = LiteLlm.generate_content_async


async def _semaphore_generate_content_async(self, *args, **kwargs):
    async with concurrency_semaphore:
        try:
            async for response in _original_generate_content_async(
                self, *args, **kwargs
            ):
                yield response
        except Exception as e:
            is_parallel_model = (
                getattr(self, "model", None) == LOCAL_PARALLEL_MODEL_NAME
            )
            if is_parallel_model and LOCAL_PARALLEL_MODEL_NAME != LOCAL_MODEL_NAME:
                print(f"⚠️ Warning: Model '{self.model}' failed with error: {e}")
                print(
                    f"👉 Falling back to aggregator model '{LOCAL_MODEL_NAME}' to process this step..."
                )

                fallback_model = LiteLlm(model=LOCAL_MODEL_NAME)
                # Call original to avoid double semaphore acquisition
                async for response in _original_generate_content_async(
                    fallback_model, *args, **kwargs
                ):
                    yield response
            else:
                raise e


LiteLlm.generate_content_async = _semaphore_generate_content_async

# Instantiate model objects
model_obj = LiteLlm(model=LOCAL_MODEL_NAME)
parallel_model_obj = LiteLlm(model=LOCAL_PARALLEL_MODEL_NAME)

print(f"✅ Aggregator Model: {LOCAL_MODEL_NAME}")
print(f"✅ Parallel Sub-agents Model: {LOCAL_PARALLEL_MODEL_NAME}")
