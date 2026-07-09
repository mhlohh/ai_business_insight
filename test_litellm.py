import asyncio
import os
import litellm
from dotenv import load_dotenv

load_dotenv(override=True)
LMSTUDIO_API_BASE = os.getenv("LMSTUDIO_API_BASE", "http://localhost:1234/v1")
LMSTUDIO_API_KEY = os.getenv("LMSTUDIO_API_KEY", "lm-studio")
LOCAL_MODEL_NAME = os.getenv("LOCAL_MODEL_NAME", "openai/qwen/qwen3.5-9b")

os.environ["OPENAI_API_BASE"] = LMSTUDIO_API_BASE
os.environ["OPENAI_API_KEY"] = LMSTUDIO_API_KEY

async def main():
    print(f"Testing {LOCAL_MODEL_NAME} with Litellm...")
    messages = [
        {"role": "user", "content": "Please output a JSON with a single key 'test' and value 'success'."}
    ]
    response_format = {
        "type": "json_schema",
        "json_schema": {
            "name": "TestSchema",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "test": {"type": "string"}
                },
                "required": ["test"],
                "additionalProperties": False
            }
        }
    }
    
    try:
        response = await litellm.acompletion(
            model=LOCAL_MODEL_NAME,
            messages=messages,
            response_format=response_format,
            temperature=0,
        )
        print("--- Raw Litellm Response ---")
        print(response)
        
        message = response.choices[0].message
        print("\n--- Message Object ---")
        print(f"Type: {type(message)}")
        print(f"Content: {getattr(message, 'content', None)}")
        print(f"Reasoning Content: {getattr(message, 'reasoning_content', None)}")
        
        # Test monkeypatch logic
        if not getattr(message, "content", None) and getattr(message, "reasoning_content", None):
            print("\nAttempting to assign reasoning_content to content...")
            message.content = message.reasoning_content
            print(f"New Content: {message.content}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
