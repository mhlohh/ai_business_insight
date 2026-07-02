# Antigravity Asyncio Pipeline Project

This project demonstrates a production-ready, non-blocking asyncio engine designed to call external APIs (such as AI models or LLM endpoints) under strict concurrency constraints, handling transient errors and timeouts gracefully.

## Project Structure

- **[mock_api.py](file:///C:/Users/Admin/OneDrive/Desktop/asyncio_pipeline_project/mock_api.py)**: Simulates a remote API server. It tracks the concurrency level of active calls, raises `RateLimitError` (HTTP 429) or `NetworkError` on initial attempts, and delays execution for specific chunks to simulate timeouts.
- **[engine.py](file:///C:/Users/Admin/OneDrive/Desktop/asyncio_pipeline_project/engine.py)**: The core engine implementing the concurrent request wrapper. It includes:
  - **`asyncio.Semaphore(5)`**: Restricts execution to a maximum of 5 concurrent requests at a time.
  - **Exponential Backoff**: When a 429 rate limit or network glitch occurs, the task waits for $2^{\text{attempt}} + \text{jitter}$ seconds and retries (up to 3 times). Crucially, the task releases the semaphore during the backoff period so other waiting tasks can utilize the slots.
  - **Timeout Protection**: Wraps requests in `asyncio.wait_for(...)`. If a request hangs past the timeout threshold (e.g., 2.5 seconds), the engine handles the `asyncio.TimeoutError` gracefully and logs the error, allowing the rest of the pipeline to proceed.
- **[run.py](file:///C:/Users/Admin/OneDrive/Desktop/asyncio_pipeline_project/run.py)**: The entry point script that spawns 12 concurrent requests and prints the execution duration and status of each task at the end.

## How to Run

Open your terminal in this directory and execute the runner script:

```bash
python run.py
```
