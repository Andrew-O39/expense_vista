import json
from typing import Optional
from app.core.config import settings

# Try new SDK (openai>=1.x)
try:
    from openai import OpenAI
    _OPENAI_STYLE = "client"
except Exception:
    OpenAI = None
    _OPENAI_STYLE = None

# Try old SDK (openai<1.x)
try:
    import openai  # old style
    if not _OPENAI_STYLE:
        _OPENAI_STYLE = "legacy"
except Exception:
    openai = None
    if not _OPENAI_STYLE:
        _OPENAI_STYLE = None

try:
    import boto3  # Bedrock
except Exception:
    boto3 = None


class AIClient:
    """Very small abstraction over providers. Returns plain text."""

    def __init__(self):
        self.provider = (settings.ai_provider or "none").lower()
        self.client = None
        self.bedrock = None

        if self.provider == "openai" and settings.openai_api_key:
            if _OPENAI_STYLE == "client" and OpenAI is not None:
                # new SDK
                self.client = OpenAI(api_key=settings.openai_api_key)
            elif _OPENAI_STYLE == "legacy" and openai is not None:
                # old SDK
                openai.api_key = settings.openai_api_key

        if self.provider == "bedrock" and boto3 and settings.bedrock_region:
            self.bedrock = boto3.client("bedrock-runtime", region_name=settings.bedrock_region)

    def enabled(self) -> bool:
        return bool(settings.ai_category_suggestion_enabled) and self.provider in {"openai", "bedrock"}

    def complete(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        if not self.enabled():
            return None

        # --- OpenAI ---
        if self.provider == "openai":
            # new SDK
            if _OPENAI_STYLE == "client" and self.client is not None:
                try:
                    resp = self.client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        temperature=0.2,
                    )
                    return (resp.choices[0].message.content or "").strip()
                except Exception:
                    return None

            # old SDK
            if _OPENAI_STYLE == "legacy" and openai is not None:
                try:
                    resp = openai.ChatCompletion.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        temperature=0.2,
                    )
                    return (resp["choices"][0]["message"]["content"] or "").strip()
                except Exception:
                    return None

        # --- Bedrock (Claude on Bedrock) ---
        if self.provider == "bedrock" and self.bedrock:
            try:
                payload = {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 100,
                    "temperature": 0.2,
                    "messages": [
                        {"role": "user", "content": f"{system_prompt}\n\n{user_prompt}"}
                    ]
                }
                res = self.bedrock.invoke_model(
                    modelId=settings.bedrock_model_id,
                    body=json.dumps(payload),
                    contentType="application/json",
                    accept="application/json",
                )
                body = res["body"].read().decode("utf-8")
                data = json.loads(body)
                return "".join([c.get("text", "") for c in data.get("content", [])]).strip()
            except Exception:
                return None

        return None


ai_client = AIClient()