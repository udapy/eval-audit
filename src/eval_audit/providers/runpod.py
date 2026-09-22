"""RunPod provider adapter for eval-audit.

Supports running model evaluation inference on RunPod:
1. RunPod Serverless Endpoints: https://api.runpod.ai/v2/{endpoint_id}/runsync
2. RunPod Pod vLLM / OpenAI-compatible servers: http://{pod_host}:{port}/v1/chat/completions

Stdlib only; zero runtime dependencies.
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.request
import urllib.error
from typing import Any


class RunPodProvider:
    """RunPod inference provider supporting serverless endpoints and pod endpoints."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        endpoint_id: str | None = None,
        pod_base_url: str | None = None,
    ) -> None:
        self.api_key = api_key or os.environ.get("RUNPOD_API_KEY", "")
        self.endpoint_id = endpoint_id or os.environ.get("RUNPOD_ENDPOINT_ID", "")
        self.pod_base_url = pod_base_url or os.environ.get("RUNPOD_POD_URL", "")

    def chat_completion(
        self,
        *,
        messages: list[dict[str, str]],
        model: str = "default",
        max_tokens: int = 128,
        temperature: float = 0.0,
        retries: int = 3,
    ) -> str:
        """Send a chat completion request to RunPod."""
        # Path A: vLLM running on RunPod Pod (OpenAI-compatible)
        if self.pod_base_url:
            url = f"{self.pod_base_url.rstrip('/')}/v1/chat/completions"
            payload = {
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
            }
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            return self._send_request(url, payload, headers, retries=retries)

        # Path B: RunPod Serverless
        if self.endpoint_id:
            if not self.api_key:
                raise ValueError("RUNPOD_API_KEY required for RunPod serverless inference.")
            url = f"https://api.runpod.ai/v2/{self.endpoint_id}/runsync"
            payload = {
                "input": {
                    "prompt": self._messages_to_prompt(messages),
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                }
            }
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            }
            return self._send_request(url, payload, headers, retries=retries)

        raise ValueError(
            "RunPod provider not configured: specify either RUNPOD_ENDPOINT_ID or RUNPOD_POD_URL."
        )

    def _send_request(
        self,
        url: str,
        payload: dict[str, Any],
        headers: dict[str, str],
        retries: int = 3,
    ) -> str:
        body = json.dumps(payload).encode("utf-8")
        for attempt in range(retries):
            try:
                req = urllib.request.Request(url, data=body, headers=headers, method="POST")
                with urllib.request.urlopen(req, timeout=60) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    # OpenAI-compatible
                    if "choices" in data and data["choices"]:
                        return data["choices"][0].get("message", {}).get("content", "")
                    # Serverless
                    if "output" in data:
                        out = data["output"]
                        if isinstance(out, dict):
                            return out.get("text", "") or out.get("content", "")
                        return str(out)
                    return json.dumps(data)
            except urllib.error.HTTPError as e:
                if e.code == 429 and attempt < retries - 1:
                    time.sleep(5 * (attempt + 1))
                else:
                    raise
            except Exception:
                if attempt < retries - 1:
                    time.sleep(3)
                else:
                    raise
        return ""

    @staticmethod
    def _messages_to_prompt(messages: list[dict[str, str]]) -> str:
        parts = []
        for m in messages:
            role = m.get("role", "user").capitalize()
            parts.append(f"{role}: {m.get('content', '')}")
        parts.append("Assistant:")
        return "\n\n".join(parts)
