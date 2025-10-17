from __future__ import annotations
import json
from typing import Any, Dict
from app.core.config import settings

_openai_client = None

def _ensure_openai():
    global _openai_client
    if _openai_client is None:
        from openai import OpenAI
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is not set.")
        _openai_client = OpenAI(api_key=settings.openai_api_key)
    return _openai_client


def llm_complete_json(prompt: str, system: str = "You extract intents as strict JSON only.") -> Dict[str, Any]:
    """
    Ask the model to return strict JSON: { intent, params }
    """
    client = _ensure_openai()
    resp = client.chat.completions.create(
        model=settings.ai_model,
        temperature=0.1,
        messages=[
            {"role": "system", "content": system + " Respond only with JSON."},
            {"role": "user", "content": prompt},
        ],
    )
    text = resp.choices[0].message.content or ""
    try:
        return json.loads(_extract_json(text))
    except Exception as e:
        raise RuntimeError(f"Failed to parse JSON from model: {e}\nRaw: {text}")


def _extract_json(s: str) -> str:
    start = s.find("{")
    end = s.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found.")
    return s[start:end + 1]