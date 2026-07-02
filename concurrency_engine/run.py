import asyncio
import time
import mock_api
from engine import process_chunk

async def main():
    print("=" * 65)
    print("Starting the Antigravity Asyncio Pipeline Simulation...")
    print("=" * 65)
    
    semaphore = asyncio.Semaphore(5)
    
    chunks = list(range(1, 13))
    
    start_time = time.time()
    
    tasks = [process_chunk(chunk_id, semaphore, timeout=2.5) for chunk_id in chunks]
    
    logging_info = "Executing concurrent tasks... (concurrency limit = 5)"
    print(logging_info)
    print("-" * 65)
    
    results = await asyncio.gather(*tasks)
    
    end_time = time.time()
    total_duration = end_time - start_time
    
    
    print("\n" + "=" * 65)
    print("Simulation Summary:")
    print("=" * 65)
    print(f"Total time elapsed: {total_duration:.2f} seconds")
    print(f"Max observed API concurrency: {mock_api.max_observed_concurrency} (Limit: 5)")
    print("-" * 65)
    print("Results:")
    for chunk_id, result in zip(chunks, results):
        status = "SUCCESS" if "FAILED" not in result else "FAILED"
        print(f"  Chunk {chunk_id:2d}: [{status:7s}] - {result}")
    print("=" * 65)

if __name__ == "__main__":
    asyncio.run(main())
