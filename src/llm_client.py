import json
import time
from typing import Any
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
from . import config

_groq = OpenAI(api_key=config.GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def chat_json(model: str, system: str, user: str, temperature: float = 0.0) -> tuple[dict, dict]:
    """Return (parsed_json, meta) where meta has model/tokens/latency_ms."""
    t0 = time.time()
    resp = _groq.chat.completions.create(
        model=model,
        temperature=temperature,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    latency_ms = int((time.time() - t0) * 1000)
    text = resp.choices[0].message.content or "{}"
    data = json.loads(text)
    meta = {
        "model": model,
        "prompt_tokens": resp.usage.prompt_tokens if resp.usage else None,
        "output_tokens": resp.usage.completion_tokens if resp.usage else None,
        "latency_ms": latency_ms,
    }
    return data, meta


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def chat_text(model: str, system: str, user: str, temperature: float = 0.5) -> tuple[str, dict]:
    t0 = time.time()
    resp = _groq.chat.completions.create(
        model=model,
        temperature=temperature,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    latency_ms = int((time.time() - t0) * 1000)
    text = resp.choices[0].message.content or ""
    meta = {
        "model": model,
        "prompt_tokens": resp.usage.prompt_tokens if resp.usage else None,
        "output_tokens": resp.usage.completion_tokens if resp.usage else None,
        "latency_ms": latency_ms,
    }
    return text, meta
