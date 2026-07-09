import os
from dotenv import load_dotenv
from google.adk.models.lite_llm import LiteLlm

load_dotenv(override=True)

# Configuration parameters for Groq models
LOCAL_MODEL_NAME = os.getenv("LOCAL_MODEL_NAME", "groq/meta-llama/llama-4-scout-17b-16e-instruct")
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

# Only add top_k if it is explicitly configured in environment
_top_k = os.getenv("MODEL_TOP_K")
if _top_k is not None:
    GENERATION_CONFIG["top_k"] = int(_top_k)
    PARALLEL_GENERATION_CONFIG["top_k"] = int(_top_k)

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
