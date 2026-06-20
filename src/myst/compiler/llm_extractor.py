import json 
import os 

import httpx

from myst.claim import Claim
from myst.methodology import MethodologySpace
from myst.compiler.extractor import ProposedPins
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("OPENROUTER_API_KEY")

DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "anthropic/claude-3.5-haiku"

SYSTEM_PROMPT = """You extract stated methodology from an earth-observation claim.

You are given a claim and a list of methodology axes. Each axis has an id and a
fixed set of allowed option values. Your job: for each axis the claim EXPLICITLY
states a choice for, return that choice. For axes the claim does not mention, do
not return anything.

Hard rules:
- Only return an axis if the claim's text explicitly commits to a value.
- The value MUST be exactly one of that axis's allowed values. Never invent one.
- When unsure, omit the axis. Omission is safe; guessing is not.
- Return ONLY JSON, no prose, no markdown fences. Schema:
  {"pins": [{"axis_id": "...", "value": ..., "source_evidence": "<quote>"}]}
"""

class LLMExtractor: 
    def __init__(self, api_key = API_KEY, model = DEFAULT_MODEL, base_url = DEFAULT_BASE_URL, client = None):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self._client = client
        self.id = f"llm:{model}"
    
    def _post(self, payload: dict) -> dict:
        client = self._client or httpx.Client(timeout = 60)
        try:
            resp = client.post(
                f"{self.base_url}/chat/completions",
                headers = {"Authorization": f"Bearer {self.api_key}"},
                json = payload
            )
            resp.raise_for_status()
            return resp.json()
        finally: 
            if self._client is None:
                client.close()
    
    def _build_axis_brief(self, methodology_space: MethodologySpace) -> str:
        lines = []
        for axis in methodology_space.axes: 
            allowed = ", ".join(str(v) for v in axis.option_values())
            lines.append(f"{axis.id}: {axis.description} -- allowed: {allowed}")
        return "\n".join(lines)
    def extract(self, claim: Claim, methodology_space: MethodologySpace) -> list[ProposedPins]:
        user_msg = (
            f"Claim: \n{claim.raw_text}\n\n"
            f"Axes: \n{self._build_axis_brief(methodology_space)}"
        )
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            "temperature": 0,
        }
        data = self._post(payload)
        content = data["choices"][0]["message"]["content"]
        return self._parse(content)
    
    @staticmethod
    def _parse(content: str) -> list[ProposedPins]:
        text = content.strip()
        if text.startswith("```"):
            text = text.split("```")[1] if "```" in text[3:] else text.strip("`")
            text = text.removeprefix("json").strip()
        try:
            parsed = json.loads(text)
            pins = parsed.get("pins", [])
        except (json.JSONDecodeError, AttributeError):
            return []
        result = []
        for p in pins:
            try: 
                result.append(
                    ProposedPins(
                        axis_id = p["axis_id"],
                        value = p["value"],
                        source_evidence = p.get("source_evidence")
                    )
                )
            except (KeyError, TypeError):
                continue
        return result





