import asyncio

class RateLimitError(Exception):
   
    pass

class NetworkError(Exception):
    
    pass


active_requests = 0
max_observed_concurrency = 0

async def simulate_api_call(chunk_id: int) -> str:
   
    global active_requests, max_observed_concurrency
    
    
    active_requests += 1
    max_observed_concurrency = max(max_observed_concurrency, active_requests)
    
    print(f"   [API Server] >>> Chunk {chunk_id} entered. Active requests: {active_requests} (Max: {max_observed_concurrency})")
    
    try:
        
        if chunk_id in [3, 7] and not hasattr(simulate_api_call, f"failed_rate_{chunk_id}"):
            setattr(simulate_api_call, f"failed_rate_{chunk_id}", True)
            raise RateLimitError("HTTP 429: Too Many Requests")
            
        if chunk_id == 5 and not hasattr(simulate_api_call, f"failed_net_{chunk_id}"):
            setattr(simulate_api_call, f"failed_net_{chunk_id}", True)
            raise NetworkError("Temporary Connection Reset")

        if chunk_id == 9:
            await asyncio.sleep(5.0)  
            return f"Chunk {chunk_id} processed (delayed)"

       
        await asyncio.sleep(0.5)
        return f"Chunk {chunk_id} processed successfully"
        
    finally:
        active_requests -= 1
        print(f"   [API Server] <<< Chunk {chunk_id} exited. Active requests: {active_requests}")
