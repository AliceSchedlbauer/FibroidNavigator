"""
WombWise voice booking via ElevenLabs text-to-speech.

Falls back gracefully when ELEVENLABS_API_KEY is not configured.
"""

from __future__ import annotations

import os
from typing import Any

import httpx

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
ELEVENLABS_MODEL_ID = os.getenv("ELEVENLABS_MODEL_ID", "eleven_multilingual_v2")
ELEVENLABS_API_URL = "https://api.elevenlabs.io/v1/text-to-speech"


def is_voice_configured() -> bool:
    return bool(ELEVENLABS_API_KEY.strip())


def voice_status() -> dict[str, Any]:
    return {
        "configured": is_voice_configured(),
        "provider": "ElevenLabs" if is_voice_configured() else "browser_fallback",
        "voice_id": ELEVENLABS_VOICE_ID if is_voice_configured() else None,
        "model_id": ELEVENLABS_MODEL_ID if is_voice_configured() else None,
    }


def synthesize_speech(text: str, timeout: float = 30.0) -> bytes:
    """Generate MP3 audio from booking script text."""
    if not is_voice_configured():
        raise RuntimeError(
            "ElevenLabs API key not configured. Set ELEVENLABS_API_KEY in your environment."
        )

    cleaned = text.strip()
    if not cleaned:
        raise ValueError("Voice script text cannot be empty.")

    url = f"{ELEVENLABS_API_URL}/{ELEVENLABS_VOICE_ID}"
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": ELEVENLABS_API_KEY,
    }
    payload = {
        "text": cleaned,
        "model_id": ELEVENLABS_MODEL_ID,
        "voice_settings": {
            "stability": 0.45,
            "similarity_boost": 0.8,
            "style": 0.2,
            "use_speaker_boost": True,
        },
    }

    with httpx.Client(timeout=timeout) as client:
        response = client.post(url, headers=headers, json=payload)
        if response.status_code == 401:
            raise RuntimeError("Invalid ElevenLabs API key.")
        if response.status_code >= 400:
            raise RuntimeError(
                f"ElevenLabs request failed ({response.status_code}): {response.text[:200]}"
            )
        return response.content
