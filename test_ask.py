import asyncio
from app.services.model_provider import ask

async def main():
    res = await ask([["This is a great product!"]])
    print("Final Result:", res)

if __name__ == "__main__":
    asyncio.run(main())
