from __future__ import annotations
import json
import re
from typing import Any, Dict
from app.core.config import settings

_openai_client = None

def _ensure_openai():
    """
    Lazily instantiate the OpenAI client. Reads API key from settings or env.
    """
    global _openai_client
    if _openai_client is None:
        try:
            from openai import OpenAI
        except Exception as e:
            raise RuntimeError(f"OpenAI SDK not installed: {e}")
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is not set.")
        # You can also just do OpenAI() if OPENAI_API_KEY is in the env
        _openai_client = OpenAI(api_key=settings.openai_api_key)
    return _openai_client


def llm_complete_json(
    prompt: str,
    system: str = "You extract intents as strict JSON only."
) -> Dict[str, Any]:
    """
    Ask the model to return strict JSON: { "intent": string, "params": object }.

    Returns {} on failure so the caller can gracefully fall back.
    """
    try:
        client = _ensure_openai()

        # Sensible default model if not set
        model = (settings.ai_model or "gpt-4o-mini").strip()

        resp = client.chat.completions.create(
            model=model,
            temperature=0.1,
            max_tokens=256,
            messages=[
                {"role": "system", "content": system + " Respond only with JSON."},
                {"role": "user", "content": prompt},
            ],
        )
        raw = resp.choices[0].message.content or ""

        # Try to parse JSON robustly
        parsed = _safe_parse_json(raw)
        if not isinstance(parsed, dict):
            return {}
        # Normalize output a bit
        intent = str(parsed.get("intent", "")).strip().lower()
        params = parsed.get("params") or {}
        if not isinstance(params, dict):
            params = {}
        return {"intent": intent, "params": params}
    except Exception as e:
        # Log server-side if you like; return {} to avoid breaking the endpoint
        print("llm_complete_json error:", repr(e))
        return {}


def _safe_parse_json(s: str) -> Any:
    """
    Try several strategies to extract valid JSON from model text:
    - Strip code fences (``` or ```json).
    - Extract the largest {...} block.
    - As a last resort, normalize quotes for simple key/value JSON.
    """
    if not s:
        return {}

    text = s.strip()

    # 1) Remove code fences if present
    # ```json ... ``` or ``` ... ```
    fenced = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
    if fenced:
        text = fenced.group(1).strip()

    # 2) Extract the outermost JSON object from the string
    try:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            candidate = text[start : end + 1]
            return json.loads(candidate)
    except Exception:
        pass

    # 3) Try direct parse (in case it was already pure JSON without braces extraction)
    try:
        return json.loads(text)
    except Exception:
        pass

    # 4) Very light repair: replace single quotes with double (only if it looks JSON-ish)
    if "{" in text and "}" in text and "'" in text and '"' not in text:
        try:
            repaired = text.replace("'", '"')
            start = repaired.find("{")
            end = repaired.rfind("}")
            if start != -1 and end != -1 and end > start:
                return json.loads(repaired[start : end + 1])
        except Exception:
            pass

    # Give up
    return {}