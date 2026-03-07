"""Ollama integration for local LLM (gemma3:4b)."""

import requests
from typing import Optional

OLLAMA_URL = "http://localhost:11434"
MODEL = "gemma3:4b"


def generate(prompt: str, system: Optional[str] = None, max_tokens: int = 1024) -> str:
    """Call Ollama API to generate text."""
    try:
        payload = {
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"num_predict": max_tokens},
        }
        if system:
            payload["system"] = system
        r = requests.post(f"{OLLAMA_URL}/api/generate", json=payload, timeout=120)
        r.raise_for_status()
        return r.json().get("response", "")
    except requests.exceptions.ConnectionError:
        return f"[Ollama not running. Start with: ollama run {MODEL}]"
    except Exception as e:
        return f"[Error: {str(e)}]"
