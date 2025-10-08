import json
from typing import Optional
from app.core.config import settings

# Optional providers
try:
    import openai  # type: ignore
except Exception:
    openai = None

try:
    import boto3  # Bedrock
except Exception:
    boto3 = None


class AIClient:
    """Very small abstraction over providers. Returns plain text."""

    def __init__(self):
        self.provider = (settings.ai_provider or "none").lower()

        if self.provider == "openai" and openai and settings.openai_api_key:
            openai.api_key = settings.openai_api_key

        if self.provider == "bedrock" and boto3 and settings.bedrock_region:
            self.bedrock = boto3.client("bedrock-runtime", region_name=settings.bedrock_region)
        else:
            self.bedrock = None

    def enabled(self) -> bool:
        return bool(settings.ai_category_suggestion_enabled) and self.provider in {"openai", "bedrock"}

    def complete(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        if not self.enabled():
            return None

        if self.provider == "openai" and openai:
            # GPT-4o-mini / gpt-4o-mini is cheap+good; adjust if you like
            resp = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
            )
            return resp.choices[0].message.content.strip()

        if self.provider == "bedrock" and self.bedrock:
            # Anthropics on Bedrock (Claude 3)
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

        return None


ai_client = AIClient()