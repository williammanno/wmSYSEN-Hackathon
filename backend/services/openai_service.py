"""OpenAI GPT-4o integration for text generation."""

import os
from pathlib import Path
from typing import Optional

import requests
from dotenv import load_dotenv

# Load env from backend/.env and repo-root/.env for flexible run locations.
service_dir = Path(__file__).resolve().parent
backend_dir = service_dir.parent
repo_root = backend_dir.parent
load_dotenv(backend_dir / ".env")
load_dotenv(repo_root / ".env")

OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")


def generate(prompt: str, system: Optional[str] = None, max_tokens: int = 1024) -> str:
    """Call OpenAI Chat Completions API to generate text."""
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return "[Missing OPENAI_API_KEY in environment/.env]"

    try:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": MODEL,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.4,
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        response = requests.post(
            OPENAI_API_URL,
            json=payload,
            headers=headers,
            timeout=120,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("choices", [{}])[0].get("message", {}).get("content", "") or ""
    except Exception as e:
        return f"[OpenAI error: {str(e)}]"
