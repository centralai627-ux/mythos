"""
Mythos API Client
=================
Talks to OpenRouter with automatic key rotation & smart retries.
User-facing model names are NEVER the underlying model ids.
"""
from __future__ import annotations
import json
import time
import threading
import requests
from typing import Optional, Dict, Any, List, Iterator, Union

from .config import config
from .key_manager import KeyManager

# --- Public model aliases (user-facing). Real ids resolved internally. ---
MODEL_ALIASES: Dict[str, str] = {
    "mythos-code": "code",   # Default for all coding/shell tasks (fastest).
    "mythos-code-alt": "code-alt",  # Alternative code model.
    "mythos-code-super": "code-super",  # Super code model (120B).
    "mythos-ultra": "ultra", # Complex reasoning fallback.
    "mythos-vision": "vision",  # Image / file analysis.
    "mythos-5": "shannon-1", # Shannon Coder 1 (primary) - branded Mythos 5.
    "mythos-5-pro": "shannon-2",  # Shannon Pro 2 (secondary) - branded Mythos 5 Pro.
}

# Aliases routed to the Shannon provider (separate base URL + key ring).
SHANNON_ALIASES = {"mythos-5", "mythos-5-pro"}


class APIError(Exception):
    """Raised when all keys are exhausted or a hard failure occurs."""
    pass


class MythosAPI:
    """
    OpenRouter chat-completion client with rolling keys.

    Each request:
      1. Pull a healthy key from the ring.
      2. POST /chat/completions.
      3. On 429/5xx -> rotate key + retry (up to `max_retries`).
      4. On 401/403 -> mark key dead + rotate.
    """

    def __init__(self, key_manager: Optional[KeyManager] = None) -> None:
        self.cfg = config
        self.keys = key_manager or KeyManager(
            self.cfg.openrouter_keys, self.cfg.zai_keys, self.cfg.notify_rolling
        )
        # Separate rolling key ring for the Shannon provider.
        self.shannon_keys = KeyManager(
            self.cfg.shannon_keys, [], self.cfg.notify_rolling
        )
        self.base_url = self.cfg.base_url.rstrip("/")
        self.shannon_base_url = self.cfg.shannon_base_url.rstrip("/")
        self.timeout = self.cfg.timeout
        self._session = requests.Session()
        self._session.headers.update({
            "Content-Type": "application/json",
            "HTTP-Referer": "https://mythos.ai/cli",
            "X-Title": "Mythos CLI",
        })
        self._lock = threading.Lock()

    # ----------------------- Helpers ----------------------- #
    def _is_shannon(self, alias: str) -> bool:
        return alias in SHANNON_ALIASES

    def _resolve_model(self, alias: str) -> str:
        """Translate user-facing alias to internal model id."""
        if self._is_shannon(alias):
            internal = MODEL_ALIASES.get(alias, "shannon-1")
            return self.cfg.get_shannon_model(internal)
        internal = MODEL_ALIASES.get(alias, alias)
        return self.cfg.get_model(internal)

    def _mask(self, key: str) -> str:
        return key[:10] + "..." + key[-4:] if len(key) > 16 else "***"

    # ----------------------- Core request ----------------------- #
    def chat(
        self,
        messages: List[Dict[str, Any]],
        model_alias: str = "mythos-code",
        *,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        max_retries: int = 8,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> Union[str, Iterator[str]]:
        """
        Send a chat completion request. Returns full text (or stream iterator).

        Silently rotates keys on failures. Never raises on 429/5xx unless all
        keys are dead — only raises APIError when nothing is recoverable.
        """
        # Route to the Shannon provider if the alias is Shannon-backed.
        if self._is_shannon(model_alias):
            return self._chat_shannon(
                messages, model_alias,
                temperature=temperature, max_tokens=max_tokens,
                stream=stream, max_retries=max_retries,
            )

        model = self._resolve_model(model_alias)
        temp = temperature if temperature is not None else self.cfg.temperature
        tokens = max_tokens or self.cfg.max_tokens

        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temp,
            "max_tokens": tokens,
        }
        if stream:
            payload["stream"] = True
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        # Reasoning models need a larger budget so the thinking phase doesn't
        # consume the entire max_tokens (leaving content empty). Boost it.
        reasoning_models = (
            "nemotron-3-ultra", "nemotron-3-nano-omni", "north-mini-code",
            "reasoning", "r1", "deepseek-r1",
        )
        if any(rm in model for rm in reasoning_models):
            payload["max_tokens"] = max(tokens, 4096)

        last_err: Optional[str] = None
        for attempt in range(max_retries):
            key = self.keys.get_openrouter_key()
            if key is None:
                # All keys exhausted — wait briefly, then retry once.
                time.sleep(min(2.0 * (attempt + 1), 10.0))
                key = self.keys.get_openrouter_key()
                if key is None:
                    raise APIError(
                        "All keys are on cooldown. Please wait a moment and retry."
                    )

            headers = {"Authorization": f"Bearer {key}"}
            try:
                if stream:
                    return self._stream_request(payload, headers, key)
                resp = self._session.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=self.timeout,
                )
            except requests.RequestException as e:
                # Network blip — small cooldown, rotate.
                self.keys.openrouter.report_generic_error(key)
                last_err = f"network: {e}"
                continue

            # ----- Response handling -----
            if resp.status_code == 200:
                self.keys.openrouter.report_success(key)
                try:
                    data = resp.json()
                    msg = data["choices"][0]["message"]
                    # Primary content.
                    content = msg.get("content")
                    # Reasoning models (cohere/north-mini-code, nvidia nemotron
                    # reasoning variants) put output in `reasoning` when the
                    # token budget is consumed by thinking. Fall back to it.
                    if not content:
                        content = msg.get("reasoning") or ""
                        # Some providers nest it under reasoning_details.
                        if not content and msg.get("reasoning_details"):
                            rd = msg["reasoning_details"]
                            if isinstance(rd, list) and rd:
                                content = rd[0].get("text", "") or ""
                    # If we still got reasoning text (no final answer) and
                    # finish_reason indicates truncation, that's acceptable —
                    # return what we have rather than empty.
                    return (content or "").strip()
                except (ValueError, KeyError, IndexError) as e:
                    last_err = f"parse: {e}"
                    continue

            if resp.status_code in (401, 403):
                self.keys.openrouter.report_dead(key)
                last_err = f"http {resp.status_code} (auth)"
                continue

            if resp.status_code == 429:
                # Parse Retry-After if present.
                cooldown = 60.0
                ra = resp.headers.get("Retry-After")
                if ra:
                    try:
                        cooldown = min(float(ra), 120.0)
                    except ValueError:
                        pass
                self.keys.openrouter.report_rate_limit(key, cooldown)
                last_err = "http 429 (rate limit)"
                continue

            if 500 <= resp.status_code < 600:
                self.keys.openrouter.report_generic_error(key)
                last_err = f"http {resp.status_code} (server)"
                continue

            # Other 4xx — treat as non-recoverable for this key.
            self.keys.openrouter.report_rate_limit(key, 30.0)
            last_err = f"http {resp.status_code}"
            continue

        raise APIError(f"Request failed after {max_retries} retries. Last: {last_err}")

    # ----------------------- Shannon provider ----------------------- #
    def _chat_shannon(
        self,
        messages: List[Dict[str, Any]],
        model_alias: str,
        *,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        max_retries: int = 8,
    ) -> str:
        """
        Chat completion via the Shannon provider (branded Mythos-5).
        OpenAI-compatible endpoint with its own key ring + rolling.
        """
        model = self._resolve_model(model_alias)
        temp = temperature if temperature is not None else self.cfg.temperature
        tokens = max_tokens or self.cfg.max_tokens

        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temp,
            "max_tokens": tokens,
        }
        if stream:
            payload["stream"] = True

        last_err: Optional[str] = None
        for attempt in range(max_retries):
            key = self.shannon_keys.get_openrouter_key()
            if key is None:
                time.sleep(min(2.0 * (attempt + 1), 10.0))
                key = self.shannon_keys.get_openrouter_key()
                if key is None:
                    raise APIError(
                        "All Shannon keys are on cooldown. Try again shortly."
                    )
            headers = {"Authorization": f"Bearer {key}"}
            try:
                resp = self._session.post(
                    f"{self.shannon_base_url}/chat/completions",
                    json=payload, headers=headers, timeout=self.timeout,
                )
            except requests.RequestException as e:
                self.shannon_keys.openrouter.report_generic_error(key)
                last_err = f"network: {e}"
                continue

            if resp.status_code == 200:
                self.shannon_keys.openrouter.report_success(key)
                try:
                    data = resp.json()
                    msg = data["choices"][0]["message"]
                    content = msg.get("content")
                    if not content:
                        # Reasoning-style models may put output in 'reasoning'.
                        content = msg.get("reasoning") or ""
                        if not content and msg.get("reasoning_details"):
                            rd = msg["reasoning_details"]
                            if isinstance(rd, list) and rd:
                                content = rd[0].get("text", "") or ""
                    return (content or "").strip()
                except (ValueError, KeyError, IndexError) as e:
                    last_err = f"parse: {e}"
                    continue

            if resp.status_code in (401, 403):
                self.shannon_keys.openrouter.report_dead(key)
                last_err = f"http {resp.status_code} (auth)"
                continue
            if resp.status_code == 429:
                cooldown = 60.0
                ra = resp.headers.get("Retry-After")
                if ra:
                    try:
                        cooldown = min(float(ra), 120.0)
                    except ValueError:
                        pass
                self.shannon_keys.openrouter.report_rate_limit(key, cooldown)
                last_err = "http 429 (rate limit)"
                continue
            if 500 <= resp.status_code < 600:
                self.shannon_keys.openrouter.report_generic_error(key)
                last_err = f"http {resp.status_code} (server)"
                continue
            self.shannon_keys.openrouter.report_rate_limit(key, 30.0)
            last_err = f"http {resp.status_code}"
            continue

        raise APIError(
            f"Shannon request failed after {max_retries} retries. Last: {last_err}"
        )

    # ----------------------- Streaming ----------------------- #
    def _stream_request(
        self, payload: Dict[str, Any], headers: Dict[str, str], key: str
    ) -> Iterator[str]:
        try:
            resp = self._session.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers,
                timeout=self.timeout,
                stream=True,
            )
        except requests.RequestException:
            self.keys.openrouter.report_generic_error(key)
            return

        if resp.status_code != 200:
            if resp.status_code in (401, 403):
                self.keys.openrouter.report_dead(key)
            elif resp.status_code == 429:
                self.keys.openrouter.report_rate_limit(key)
            else:
                self.keys.openrouter.report_generic_error(key)
            return

        self.keys.openrouter.report_success(key)
        try:
            for line in resp.iter_lines(decode_unicode=True):
                if not line or not line.startswith("data:"):
                    continue
                chunk = line[5:].strip()
                if chunk == "[DONE]":
                    break
                try:
                    obj = json.loads(chunk)
                    delta = obj["choices"][0].get("delta", {})
                    piece = delta.get("content")
                    if piece:
                        yield piece
                except (ValueError, KeyError, IndexError):
                    continue
        finally:
            resp.close()

    # ----------------------- Vision ----------------------- #
    def vision(
        self,
        prompt: str,
        image_url: Optional[str] = None,
        image_base64: Optional[str] = None,
        mime: str = "image/png",
        max_tokens: Optional[int] = 2048,
    ) -> str:
        """Send an image + prompt to Mythos-Vision."""
        if not image_url and not image_base64:
            raise APIError("vision() requires image_url or image_base64.")

        if image_url:
            img_field: Any = {"type": "image_url", "image_url": {"url": image_url}}
        else:
            img_field = {
                "type": "image_url",
                "image_url": {"url": f"data:{mime};base64,{image_base64}"},
            }

        messages = [{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                img_field,
            ],
        }]
        return self.chat(
            messages, model_alias="mythos-vision",
            max_tokens=max_tokens, temperature=0.3,
        )
