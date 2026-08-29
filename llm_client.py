"""
llm_client.py — Gayatri AI v5.0
Thin wrapper around the LM Studio OpenAI-compatible REST API.
Replaces the legacy Ollama client entirely. No other module should
call `requests` directly against the LLM server — always go through here.
"""

import json
import requests

import config


class LMStudioError(Exception):
    """Raised when LM Studio is unreachable or returns an unexpected payload."""
    pass


class LLMClient:
    def __init__(self, base_url: str = None):
        self.base_url = (base_url or config.LMSTUDIO_BASE_URL).rstrip("/")

    # ------------------------------------------------------------------
    # Connectivity / model listing
    # ------------------------------------------------------------------
    def is_reachable(self) -> bool:
        try:
            resp = requests.get(
                f"{self.base_url}{config.LMSTUDIO_MODELS_ENDPOINT}",
                timeout=config.HTTP_TIMEOUT,
            )
            return resp.status_code == 200
        except requests.RequestException:
            return False

    def list_models(self) -> list[str]:
        """Returns a list of model id strings from GET /models. Raises LMStudioError on failure."""
        try:
            resp = requests.get(
                f"{self.base_url}{config.LMSTUDIO_MODELS_ENDPOINT}",
                timeout=config.HTTP_TIMEOUT,
            )
            resp.raise_for_status()
        except requests.RequestException as e:
            raise LMStudioError(
                f"LM Studio not running at {self.base_url}. Start the server and click Refresh."
            ) from e

        try:
            data = resp.json()
            models = [item["id"] for item in data.get("data", []) if "id" in item]
        except (ValueError, KeyError, TypeError) as e:
            raise LMStudioError(f"Unexpected /models response format: {e}") from e

        return models

    # ------------------------------------------------------------------
    # Streaming chat completion
    # ------------------------------------------------------------------
    def stream_chat(self, model: str, messages: list[dict], temperature: float = None,
                     max_tokens: int = None):
        """
        Generator yielding text deltas as they arrive from LM Studio's SSE stream.
        Usage:
            for chunk in client.stream_chat(model, messages):
                ui_bubble.append(chunk)
        """
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature if temperature is not None else config.STREAM_TEMP,
            "max_tokens": max_tokens if max_tokens is not None else config.MAX_TOKENS_CHAT,
            "stream": True,
        }

        try:
            resp = requests.post(
                f"{self.base_url}{config.LMSTUDIO_CHAT_ENDPOINT}",
                json=payload,
                stream=True,
                timeout=config.LLM_TIMEOUT,
            )
            resp.raise_for_status()
        except requests.RequestException as e:
            raise LMStudioError(
                f"LM Studio not running at {self.base_url}. Start the server and click Refresh."
            ) from e

        try:
            for raw_line in resp.iter_lines(decode_unicode=True):
                if not raw_line:
                    continue
                if not raw_line.startswith("data:"):
                    continue

                data_str = raw_line[len("data:"):].strip()
                if data_str == "[DONE]":
                    break

                try:
                    chunk = json.loads(data_str)
                except json.JSONDecodeError:
                    continue

                choices = chunk.get("choices") or []
                if not choices:
                    continue

                delta = choices[0].get("delta") or {}
                content = delta.get("content")
                if content:
                    yield content
        finally:
            try:
                resp.close()
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Non-streaming chat completion (used by search gate, keyword gen)
    # ------------------------------------------------------------------
    def chat(self, model: str, messages: list[dict], temperature: float = None,
              max_tokens: int = None) -> str:
        """Returns the full response text (non-streaming). Raises LMStudioError on failure."""
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature if temperature is not None else config.GATE_TEMP,
            "max_tokens": max_tokens if max_tokens is not None else config.MAX_TOKENS_GATE,
            "stream": False,
        }

        try:
            resp = requests.post(
                f"{self.base_url}{config.LMSTUDIO_CHAT_ENDPOINT}",
                json=payload,
                timeout=config.LLM_TIMEOUT,
            )
            resp.raise_for_status()
        except requests.RequestException as e:
            raise LMStudioError(
                f"LM Studio not running at {self.base_url}. Start the server and click Refresh."
            ) from e

        try:
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError, TypeError) as e:
            raise LMStudioError(f"Unexpected /chat/completions response format: {e}") from e

    # ------------------------------------------------------------------
    # JSON-mode helper — for search gate + keyword generation
    # ------------------------------------------------------------------
    def chat_json(self, model: str, messages: list[dict], temperature: float = None,
                   max_tokens: int = None) -> dict:
        """
        Calls chat() and strictly parses the result as JSON. Used by
        search_engine.llm_gate_enhanced and search_engine.gen_keywords_enhanced,
        which both instruct the model (via system prompt) to return JSON only.
        Raises LMStudioError if the model's output is not valid JSON.
        """
        raw = self.chat(model, messages, temperature=temperature, max_tokens=max_tokens)

        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            if cleaned.lower().startswith("json"):
                cleaned = cleaned[4:]
            cleaned = cleaned.strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            raise LMStudioError(
                f"Model did not return valid JSON. Raw output: {raw[:200]}"
            ) from e
