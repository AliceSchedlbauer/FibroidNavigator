import { useEffect, useRef, useState } from "react";

const API_BASE = import.meta.env.VITE_API_URL ?? "";

function speakWithBrowser(text) {
  return new Promise((resolve, reject) => {
    if (!window.speechSynthesis) {
      reject(new Error("Browser speech synthesis is not available."));
      return;
    }

    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "en-US";
    utterance.rate = 0.95;
    utterance.pitch = 1.02;
    utterance.onend = () => resolve("browser");
    utterance.onerror = () => reject(new Error("Browser voice playback failed."));
    window.speechSynthesis.speak(utterance);
  });
}

function VoiceBooking({ script, label = "Voice booking demo" }) {
  const audioRef = useRef(null);
  const [status, setStatus] = useState("idle");
  const [mode, setMode] = useState(null);
  const [error, setError] = useState(null);
  const [voiceReady, setVoiceReady] = useState(false);

  useEffect(() => {
    let active = true;

    fetch(`${API_BASE}/api/v1/voice/status`)
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (active && data?.configured) {
          setVoiceReady(true);
        }
      })
      .catch(() => {});

    return () => {
      active = false;
      if (audioRef.current) {
        audioRef.current.pause();
        URL.revokeObjectURL(audioRef.current.src);
      }
      window.speechSynthesis?.cancel();
    };
  }, []);

  const stopPlayback = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
    }
    window.speechSynthesis?.cancel();
    setStatus("idle");
  };

  const playVoice = async () => {
    if (!script?.trim()) {
      return;
    }

    setError(null);
    setStatus("loading");
    stopPlayback();

    try {
      const response = await fetch(`${API_BASE}/api/v1/voice/speak`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: script }),
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const audio = new Audio(url);
        audioRef.current = audio;
        audio.onended = () => {
          setStatus("idle");
          URL.revokeObjectURL(url);
        };
        audio.onerror = () => {
          setStatus("idle");
          setError("Could not play ElevenLabs audio.");
          URL.revokeObjectURL(url);
        };
        await audio.play();
        setMode("elevenlabs");
        setStatus("playing");
        return;
      }

      const detail = await response.json().catch(() => ({}));
      if (response.status !== 503) {
        throw new Error(detail.detail ?? `Voice request failed (${response.status})`);
      }
    } catch (err) {
      if (!window.speechSynthesis) {
        setError(err.message);
        setStatus("idle");
        return;
      }
    }

    try {
      await speakWithBrowser(script);
      setMode("browser");
      setStatus("idle");
    } catch (err) {
      setError(err.message);
      setStatus("idle");
    }
  };

  return (
    <div className="voice-booking-card">
      <div className="voice-booking-header">
        <span className="voice-label">{label}</span>
        {voiceReady ? (
          <span className="voice-provider-pill">ElevenLabs ready</span>
        ) : (
          <span className="voice-provider-pill voice-provider-fallback">Browser voice</span>
        )}
      </div>

      <blockquote className="voicing-script">{script}</blockquote>

      <div className="voice-actions">
        <button
          type="button"
          className="btn-primary voice-play-btn"
          onClick={status === "playing" ? stopPlayback : playVoice}
          disabled={status === "loading"}
        >
          {status === "loading"
            ? "Generating voice…"
            : status === "playing"
              ? "Stop voice"
              : "▶ Listen with WombWise Voice"}
        </button>
        {mode && status !== "loading" && (
          <span className="voice-mode-note">
            {mode === "elevenlabs"
              ? "Playing via ElevenLabs"
              : "Playing via browser voice (demo fallback)"}
          </span>
        )}
      </div>

      {error && <p className="voice-error">{error}</p>}
    </div>
  );
}

export default VoiceBooking;
