import asyncio
import google.generativeai as genai
from bot.config import settings

async def test_gemini():
    print(f"Testing Gemini with key: {settings.GEMINI_API_KEY[:10]}...")
    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel(settings.GEMINI_MODEL)
    try:
        response = model.generate_content("Hello! Are you working?")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Gemini error: {e}")

if __name__ == "__main__":
    asyncio.run(test_gemini())
