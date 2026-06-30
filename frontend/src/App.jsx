import React, { useEffect, useMemo, useState } from "react";
import {
  AlertCircle,
  Download,
  FileAudio,
  Languages,
  Loader2,
  Mic2,
  PlayCircle,
  Sparkles,
  SlidersHorizontal,
} from "lucide-react";

const API_BASE_URL = (import.meta.env.VITE_API_URL || "http://localhost:8000").replace(/\/$/, "");
const API_HEADERS = {
  "ngrok-skip-browser-warning": "true",
};

const FALLBACK_LANGUAGES = [
  { code: "hi", name: "Hindi" },
  { code: "te", name: "Telugu" },
  { code: "kn", name: "Kannada" },
  { code: "fr", name: "French" },
  { code: "es", name: "Spanish" },
];

const FALLBACK_MODULATION_PRESETS = [
  { code: "natural", name: "Natural" },
  { code: "expressive", name: "Expressive" },
  { code: "steady", name: "Steady" },
  { code: "dramatic", name: "Dramatic" },
];

function App() {
  const [mediaFile, setMediaFile] = useState(null);
  const [languages, setLanguages] = useState(FALLBACK_LANGUAGES);
  const [targetLanguage, setTargetLanguage] = useState("hi");
  const [voices, setVoices] = useState([]);
  const [modulationPresets, setModulationPresets] = useState(FALLBACK_MODULATION_PRESETS);
  const [voiceId, setVoiceId] = useState("");
  const [deliveryMode, setDeliveryMode] = useState("selected_voice");
  const [modulationPreset, setModulationPreset] = useState("natural");
  const [loadingVoices, setLoadingVoices] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);
  const [audioObjectUrl, setAudioObjectUrl] = useState("");

  useEffect(() => {
    async function loadInitialData() {
      try {
        const [languagesResponse, voicesResponse] = await Promise.all([
          fetch(`${API_BASE_URL}/languages`, { headers: API_HEADERS }),
          fetch(`${API_BASE_URL}/voices`, { headers: API_HEADERS }),
        ]);
        const presetsResponse = await fetch(`${API_BASE_URL}/modulation-presets`, {
          headers: API_HEADERS,
        });

        if (languagesResponse.ok) {
          setLanguages(await languagesResponse.json());
        }

        if (presetsResponse.ok) {
          setModulationPresets(await presetsResponse.json());
        }

        if (!voicesResponse.ok) {
          const payload = await voicesResponse.json().catch(() => null);
          throw new Error(payload?.detail || "Unable to fetch ElevenLabs voices.");
        }

        const voiceData = await voicesResponse.json();
        setVoices(voiceData);
        setVoiceId(voiceData[0]?.voice_id || "");
      } catch (loadError) {
        setError(loadError.message);
      } finally {
        setLoadingVoices(false);
      }
    }

    loadInitialData();
  }, []);

  const outputAudioUrl = useMemo(() => {
    if (!result?.output_audio_url) {
      return "";
    }

    return `${API_BASE_URL}${result.output_audio_url}`;
  }, [result]);

  useEffect(() => {
    if (!outputAudioUrl) {
      setAudioObjectUrl("");
      return undefined;
    }

    let objectUrl = "";
    let cancelled = false;

    async function loadAudio() {
      try {
        const response = await fetch(outputAudioUrl, { headers: API_HEADERS });

        if (!response.ok) {
          throw new Error("Dubbed audio was generated, but the browser could not load it.");
        }

        const audioBlob = await response.blob();
        objectUrl = URL.createObjectURL(audioBlob);

        if (!cancelled) {
          setAudioObjectUrl(objectUrl);
        }
      } catch (audioError) {
        if (!cancelled) {
          setError(audioError.message);
        }
      }
    }

    loadAudio();

    return () => {
      cancelled = true;
      if (objectUrl) {
        URL.revokeObjectURL(objectUrl);
      }
    };
  }, [outputAudioUrl]);

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setResult(null);

    if (!mediaFile) {
      setError("Please upload an English audio or video file.");
      return;
    }

    if (deliveryMode === "selected_voice" && !voiceId) {
      setError("Please select an ElevenLabs voice.");
      return;
    }

    const formData = new FormData();
    formData.append("audio_file", mediaFile);
    formData.append("target_language", targetLanguage);
    formData.append("voice_id", voiceId);
    formData.append("delivery_mode", deliveryMode);
    formData.append("modulation_preset", modulationPreset);

    setSubmitting(true);

    try {
      const response = await fetch(`${API_BASE_URL}/dub`, {
        method: "POST",
        headers: API_HEADERS,
        body: formData,
      });

      const payload = await response.json().catch(() => null);

      if (!response.ok) {
        throw new Error(payload?.detail || "Dubbing failed. Please try again.");
      }

      setResult(payload);
    } catch (submitError) {
      setError(submitError.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="app-shell">
      <section className="workspace">
        <div className="header">
          <div>
            <p className="eyebrow">Interview MVP</p>
            <h1>AI Dubbing Tool</h1>
          </div>
          <div className="status-pill">
            <Sparkles size={16} />
            Whisper + NLLB + ElevenLabs
          </div>
        </div>

        <div className="content-grid">
          <form className="panel controls-panel" onSubmit={handleSubmit}>
            <div className="field">
              <label htmlFor="audio">English audio or video</label>
              <label className="file-drop" htmlFor="audio">
                <FileAudio size={28} />
                <span>{mediaFile ? mediaFile.name : "Choose a media file"}</span>
                <small>MP3, WAV, M4A, MP4, MOV, or other Whisper-supported media</small>
              </label>
              <input
                id="audio"
                type="file"
                accept="audio/*,video/*"
                onChange={(event) => setMediaFile(event.target.files?.[0] || null)}
              />
            </div>

            <div className="two-column">
              <div className="field">
                <label htmlFor="delivery">
                  <SlidersHorizontal size={16} />
                  Delivery mode
                </label>
                <select
                  id="delivery"
                  value={deliveryMode}
                  onChange={(event) => setDeliveryMode(event.target.value)}
                >
                  <option value="selected_voice">Use selected voice</option>
                  <option value="preserve_original">Preserve original delivery</option>
                </select>
              </div>

              <div className="field">
                <label htmlFor="language">
                  <Languages size={16} />
                  Target language
                </label>
                <select
                  id="language"
                  value={targetLanguage}
                  onChange={(event) => setTargetLanguage(event.target.value)}
                >
                  {languages.map((language) => (
                    <option key={language.code} value={language.code}>
                      {language.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="field">
                <label htmlFor="voice">
                  <Mic2 size={16} />
                  ElevenLabs voice
                </label>
                <select
                  id="voice"
                  value={voiceId}
                  onChange={(event) => setVoiceId(event.target.value)}
                  disabled={
                    deliveryMode === "preserve_original" ||
                    loadingVoices ||
                    voices.length === 0
                  }
                >
                  {deliveryMode === "preserve_original" && (
                    <option>Uses original speaker style</option>
                  )}
                  {loadingVoices && <option>Loading voices...</option>}
                  {!loadingVoices && voices.length === 0 && <option>No voices found</option>}
                  {voices.map((voice) => (
                    <option key={voice.voice_id} value={voice.voice_id}>
                      {voice.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="field">
                <label htmlFor="modulation">
                  <SlidersHorizontal size={16} />
                  Extra modulation
                </label>
                <select
                  id="modulation"
                  value={modulationPreset}
                  onChange={(event) => setModulationPreset(event.target.value)}
                  disabled={deliveryMode === "preserve_original"}
                >
                  {deliveryMode === "preserve_original" && (
                    <option>Original delivery preserved</option>
                  )}
                  {modulationPresets.map((preset) => (
                    <option key={preset.code} value={preset.code}>
                      {preset.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {error && (
              <div className="error-box">
                <AlertCircle size={18} />
                <span>{error}</span>
              </div>
            )}

            <button
              className="primary-button"
              type="submit"
              disabled={submitting || loadingVoices}
            >
              {submitting ? <Loader2 className="spin" size={18} /> : <PlayCircle size={18} />}
              {submitting ? "Generating dubbed audio..." : "Generate Dubbed Audio"}
            </button>
          </form>

          <section className="panel result-panel">
            {!result && !submitting && (
              <div className="empty-state">
                <PlayCircle size={42} />
                <h2>Dubbed output appears here</h2>
                <p>
                  Upload English media, select a target language and voice, then generate the
                  dubbed MP3.
                </p>
              </div>
            )}

            {submitting && (
              <div className="empty-state">
                <Loader2 className="spin" size={42} />
                <h2>Building your dubbed audio</h2>
                <p>
                  {deliveryMode === "preserve_original"
                    ? "Whisper and NLLB prepare the text while ElevenLabs preserves the source delivery."
                    : "Whisper transcribes, NLLB translates locally, and ElevenLabs renders the voice."}
                </p>
              </div>
            )}

            {result && (
              <div className="result-stack">
                <div className="text-block">
                  <h2>English transcript</h2>
                  <p>{result.original_transcript}</p>
                </div>

                <div className="text-block">
                  <h2>Translated text</h2>
                  <p>{result.translated_text}</p>
                </div>

                <div className="audio-block">
                  <h2>Dubbed audio</h2>
                  <audio controls src={audioObjectUrl}>
                    Your browser does not support the audio element.
                  </audio>
                  {result.timings && (
                    <p className="timing-text">
                      {result.delivery_mode === "preserve_original"
                        ? "Preserved original delivery"
                        : "Generated with selected voice"}{" "}
                      in {result.timings.total_seconds}s
                    </p>
                  )}
                  <a className="download-link" href={audioObjectUrl || outputAudioUrl} download>
                    <Download size={17} />
                    Download MP3
                  </a>
                </div>
              </div>
            )}
          </section>
        </div>
      </section>
    </main>
  );
}

export default App;
