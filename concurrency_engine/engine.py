import asyncio
import random
import logging
from mock_api import simulate_api_call, RateLimitError, NetworkError

# Set up logging to show timestamp and logs clearly
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)

async def process_chunk(chunk_id: int, semaphore: asyncio.Semaphore, timeout: float = 2.5) -> str:
    
    max_retries = 3
    
    for attempt in range(max_retries + 1):
        try:
            
            async with semaphore:
                logging.info(f"[Engine] Chunk {chunk_id}: Acquiring slot. Attempt {attempt + 1}/{max_retries + 1}")
                
                result = await asyncio.wait_for(simulate_api_call(chunk_id), timeout=timeout)
                
                logging.info(f"[Engine] Chunk {chunk_id}: Succeeded on attempt {attempt + 1}")
                return result
                
        except asyncio.TimeoutError:
            # 3. Graceful Timeout Handling
            logging.error(f"[Engine] Chunk {chunk_id}: TIMED OUT after {timeout} seconds on attempt {attempt + 1}")
            # We fail gracefully and return a descriptive status so we don't halt the entire pipeline
            return f"Chunk {chunk_id} FAILED: TimeoutError"
            
        except (RateLimitError, NetworkError) as e:
            # 4. Retry Loop with Exponential Backoff
            logging.warning(f"[Engine] Chunk {chunk_id}: Failed attempt {attempt + 1} with error: {e}")
            
            if attempt == max_retries:
                logging.error(f"[Engine] Chunk {chunk_id}: Exceeded max retries of {max_retries}. Final Error.")
                return f"Chunk {chunk_id} FAILED: Max retries exceeded ({e})"
            
            # Calculate exponential backoff delay: 2^attempt + jitter
            # Attempt 0 -> wait ~1s, Attempt 1 -> wait ~2s, Attempt 2 -> wait ~4s
            backoff_delay = (2 ** attempt) + random.uniform(0.1, 0.4)
            logging.info(f"[Engine] Chunk {chunk_id}: Retrying in {backoff_delay:.2f} seconds...")
            await asyncio.sleep(backoff_delay)
            
        except Exception as e:
            # Catches any unexpected general exceptions
            logging.error(f"[Engine] Chunk {chunk_id}: Encountered unexpected exception: {e}")
            return f"Chunk {chunk_id} FAILED: {e}"
