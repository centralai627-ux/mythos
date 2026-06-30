"""
Xiaomi MiMo API Integration
============================
Integrates Xiaomi MiMo models for chat, vision, and voice.
API is OpenAI-compatible.
"""
from __future__ import annotations
import os
import json
import base64
import requests
from typing import Optional, List, Dict, Any, Iterator
from dataclasses import dataclass


# MiMo API Configuration
MIMO_BASE_URL = "https://api.xiaomimimo.com/v1"

# MiMo Models
MIMO_MODELS = {
    # Chat models
    "mimo-v2-pro": "mimo-v2-pro",
    "mimo-v2-omni": "mimo-v2-omni",
    "mimo-v2-flash": "mimo-v2-flash",
    
    # TTS models
    "mimo-v2-tts": "mimo-v2-tts",
    "mimo-v2.5-tts": "mimo-v2.5-tts",
    
    # ASR models
    "mimo-v2.5-asr": "mimo-v2.5-asr",
}


@dataclass
class TTSResult:
    """Result from TTS API."""
    success: bool
    audio_data: Optional[bytes] = None
    error: Optional[str] = None
    duration: Optional[float] = None


class MiMoAPI:
    """Xiaomi MiMo API client."""
    
    def __init__(self, api_keys: List[str] = None) -> None:
        self.api_keys = api_keys or []
        self.current_key_index = 0
        self.base_url = MIMO_BASE_URL
        self._session = requests.Session()
        self._session.headers.update({
            "Content-Type": "application/json",
        })
    
    def _get_key(self) -> str:
        """Get current API key with rotation."""
        if not self.api_keys:
            raise ValueError("No MiMo API keys configured")
        key = self.api_keys[self.current_key_index]
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        return key
    
    def _make_request(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make API request with key rotation."""
        key = self._get_key()
        headers = {
            "Authorization": f"Bearer {key}",
        }
        
        url = f"{self.base_url}/{endpoint}"
        
        try:
            response = self._session.post(
                url,
                json=data,
                headers=headers,
                timeout=60,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            # Try with next key on 401/429
            if response.status_code in [401, 429] and len(self.api_keys) > 1:
                key = self._get_key()
                headers["Authorization"] = f"Bearer {key}"
                response = self._session.post(
                    url,
                    json=data,
                    headers=headers,
                    timeout=60,
                )
                response.raise_for_status()
                return response.json()
            raise
        except Exception as e:
            return {"error": str(e)}
    
    # ==================== Chat API ==================== #
    
    def chat(
        self,
        messages: List[Dict[str, Any]],
        model: str = "mimo-v2-pro",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = False,
    ) -> str:
        """Send chat completion request to MiMo."""
        data = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
        }
        
        if stream:
            return self._stream_chat(data)
        
        result = self._make_request("chat/completions", data)
        
        if "error" in result:
            return f"Error: {result['error']}"
        
        try:
            return result["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            return f"Error parsing response: {e}"
    
    def _stream_chat(self, data: Dict[str, Any]) -> Iterator[str]:
        """Stream chat response."""
        key = self._get_key()
        headers = {
            "Authorization": f"Bearer {key}",
        }
        
        url = f"{self.base_url}/chat/completions"
        
        try:
            response = self._session.post(
                url,
                json=data,
                headers=headers,
                timeout=60,
                stream=True,
            )
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    line = line.decode("utf-8")
                    if line.startswith("data: "):
                        line = line[6:]
                    if line.strip() == "[DONE]":
                        break
                    try:
                        chunk = json.loads(line)
                        if "choices" in chunk and len(chunk["choices"]) > 0:
                            delta = chunk["choices"][0].get("delta", {})
                            if "content" in delta:
                                yield delta["content"]
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            yield f"Error: {e}"
    
    # ==================== Vision API ==================== #
    
    def vision(
        self,
        prompt: str,
        image_base64: str = None,
        image_url: str = None,
        model: str = "mimo-v2-omni",
        max_tokens: int = 2048,
    ) -> str:
        """Send vision request to MiMo."""
        content = [{"type": "text", "text": prompt}]
        
        if image_base64:
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{image_base64}"}
            })
        elif image_url:
            content.append({
                "type": "image_url",
                "image_url": {"url": image_url}
            })
        
        data = {
            "model": model,
            "messages": [{"role": "user", "content": content}],
            "max_tokens": max_tokens,
        }
        
        result = self._make_request("chat/completions", data)
        
        if "error" in result:
            return f"Error: {result['error']}"
        
        try:
            return result["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            return f"Error parsing response: {e}"
    
    # ==================== TTS API ==================== #
    
    def tts(
        self,
        text: str,
        model: str = None,
        voice: str = None,
        speed: float = 1.0,
        output_format: str = "wav",
        max_retries: int = 2,
    ) -> TTSResult:
        """Convert text to speech using MiMo TTS.
        
        MiMo TTS uses Chat Completions API format:
        - user message: style/tone instructions
        - assistant message: text to speak
        - audio field: format and voice settings
        
        Uses voice design model for English (Sister Location style).
        """
        import base64
        import time
        import random
        
        # Detect language (simple heuristic)
        has_indonesian = bool(re.search(r'[a-z]+ (adalah|dan|ini|itu|untuk|dengan|tidak|bisa|akan|sudah|yang|dari|ke|di|pada)', text, re.IGNORECASE))
        
        # Use voice design model for English, regular TTS for Indonesian
        if model is None:
            model = 'mimo-v2.5-tts' if has_indonesian else 'mimo-v2.5-tts-voicedesign'
        
        if voice is None:
            voice = '冰糖' if has_indonesian else 'Mia'
        
        style_instruction = (
            'Berbicara dengan jelas, natural, dan profesional dalam Bahasa Indonesia. '
            'Gunakan intonasi yang tepat dan pengucapan yang benar.'
            if has_indonesian else
            'A cold, eerie, robotic female AI voice like Circus Baby from Five Nights at Freddy\'s Sister Location. '
            'Mechanical yet polite, unsettling calm, slightly distorted with a hint of malice beneath a friendly facade. '
            'Slow deliberate pacing, every word precisely articulated like a sophisticated AI speaking to humans it finds... interesting.'
        )
        
        # MiMo TTS uses Chat Completions API format
        messages = [
            {"role": "user", "content": style_instruction},
            {"role": "assistant", "content": text}
        ]
        
        audio_config = (
            {"format": output_format, "voice": voice}
            if has_indonesian else
            {"format": output_format, "optimize_text_preview": True}
        )
        
        data = {
            "model": model,
            "messages": messages,
            "audio": audio_config
        }
        
        key = self._get_key()
        headers = {"Authorization": f"Bearer {key}"}
        url = f"{self.base_url}/chat/completions"
        
        for attempt in range(max_retries + 1):
            try:
                response = self._session.post(
                    url,
                    json=data,
                    headers=headers,
                    timeout=60,
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if (result.get('choices') and 
                        result['choices'][0].get('message') and 
                        result['choices'][0]['message'].get('audio')):
                        
                        audio_base64 = result['choices'][0]['message']['audio']['data']
                        audio_data = base64.b64decode(audio_base64)
                        
                        return TTSResult(
                            success=True,
                            audio_data=audio_data,
                            duration=len(audio_data) / 32000,
                        )
                    else:
                        return TTSResult(success=False, error="No audio in response")
                
                elif response.status_code in [429, 503] and attempt < max_retries:
                    # Rate limited or service busy - retry with exponential backoff
                    delay = min(5 * (2 ** attempt) + random.uniform(0, 2), 20)
                    time.sleep(delay)
                    continue
                else:
                    return TTSResult(success=False, error=f"TTS API error {response.status_code}")
                    
            except Exception as e:
                if attempt < max_retries:
                    time.sleep(2)
                    continue
                return TTSResult(success=False, error=str(e))
        
        return TTSResult(success=False, error="Max retries exceeded")
    
    def tts_stream(
        self,
        text: str,
        model: str = "mimo-v2.5-tts",
        voice: str = "default",
        speed: float = 1.0,
    ) -> Iterator[bytes]:
        """Stream TTS audio."""
        data = {
            "model": model,
            "input": text,
            "voice": voice,
            "speed": speed,
            "stream": True,
        }
        
        key = self._get_key()
        headers = {
            "Authorization": f"Bearer {key}",
        }
        
        url = f"{self.base_url}/audio/speech"
        
        try:
            response = self._session.post(
                url,
                json=data,
                headers=headers,
                timeout=60,
                stream=True,
            )
            response.raise_for_status()
            
            for chunk in response.iter_content(chunk_size=4096):
                if chunk:
                    yield chunk
        except Exception as e:
            raise
    
    # ==================== ASR API ==================== #
    
    def asr(
        self,
        audio_data: bytes,
        model: str = "mimo-v2.5-asr",
        language: str = "zh",
    ) -> str:
        """Transcribe audio to text using MiMo ASR."""
        key = self._get_key()
        headers = {
            "Authorization": f"Bearer {key}",
        }
        
        url = f"{self.base_url}/audio/transcriptions"
        
        files = {
            "file": ("audio.wav", audio_data, "audio/wav"),
        }
        data = {
            "model": model,
            "language": language,
        }
        
        try:
            response = self._session.post(
                url,
                headers=headers,
                files=files,
                data=data,
                timeout=60,
            )
            response.raise_for_status()
            result = response.json()
            return result.get("text", "")
        except Exception as e:
            return f"Error: {e}"
    
    # ==================== Model Info ==================== #
    
    def list_models(self) -> List[str]:
        """List available MiMo models."""
        result = self._make_request("models", {})
        if "error" in result:
            return list(MIMO_MODELS.keys())
        
        try:
            return [m["id"] for m in result.get("data", [])]
        except (KeyError, IndexError):
            return list(MIMO_MODELS.keys())
    
    def get_model_info(self, model: str) -> Dict[str, Any]:
        """Get model information."""
        result = self._make_request(f"models/{model}", {})
        if "error" in result:
            return {"id": model, "error": result["error"]}
        return result


# Global instance
mimo_api = MiMoAPI()
