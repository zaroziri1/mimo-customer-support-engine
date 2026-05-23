"""MiMo LLM client — integration with MiMo v2.5 Pro."""
import logging
from openai import AsyncOpenAI
from src.config import MIMO_API_ENDPOINT, MIMO_MODEL, MIMO_API_KEY

logger = logging.getLogger(__name__)

_client = None


def get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            base_url=MIMO_API_ENDPOINT,
            api_key=MIMO_API_KEY,
        )
    return _client


async def mimo_chat(prompt: str, system_prompt: str = None, max_tokens: int = 2000, temperature: float = 0.3) -> str:
    """Send a chat completion request to MiMo LLM."""
    client = get_client()
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    try:
        response = await client.chat.completions.create(
            model=MIMO_MODEL,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"MiMo API error: {e}")
        return f"Error communicating with MiMo: {str(e)}"


async def mimo_stream(prompt: str, system_prompt: str = None):
    """Stream responses from MiMo LLM."""
    client = get_client()
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    try:
        stream = await client.chat.completions.create(
            model=MIMO_MODEL,
            messages=messages,
            max_tokens=2000,
            temperature=0.3,
            stream=True,
        )
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    except Exception as e:
        logger.error(f"MiMo streaming error: {e}")
        yield f"Error: {str(e)}"
