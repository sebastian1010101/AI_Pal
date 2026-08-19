"use client";

import { FormEvent, useCallback, useEffect, useRef, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL;
const REQUEST_TIMEOUT_MS = 45_000;
const IDENTITY_STORAGE_KEY = "ai-pal-identity-id";

interface Message {
  id: string;
  role: "user" | "assistant";
  text: string;
}

interface PipelineTimings {
  stt_ms: number;
  memory_ms: number;
  llm_ms: number;
  tts_ms: number;
  backend_total_ms: number;
}

interface MessageResponse {
  text: string;
  transcript: string;
  audio_base64: string | null;
  audio_error: string | null;
  timings: PipelineTimings;
}

class BackendError extends Error {}

async function fetchWithTimeout(path: string, options: RequestInit): Promise<Response> {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  try {
    return await fetch(`${API_URL}${path}`, { ...options, signal: controller.signal });
  } finally {
    window.clearTimeout(timeout);
  }
}

async function responseError(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as { detail?: string };
    if (body.detail) {
      return body.detail;
    }
  } catch {
    return `El backend respondió con un error (${response.status}).`;
  }

  return `El backend respondió con un error (${response.status}).`;
}

function requestError(error: unknown): string {
  if (error instanceof DOMException && error.name === "AbortError") {
    return "La solicitud tardó más de 45 segundos. Revisá el backend e intentá nuevamente.";
  }

  return "No pudimos conectar con el backend. Revisá tu conexión e intentá nuevamente.";
}

function blobToDataUrl(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onloadend = () => resolve(reader.result as string);
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(blob);
  });
}

export default function Home() {
  const [identityId, setIdentityId] = useState<string | null>(null);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [sessionLoading, setSessionLoading] = useState(true);
  const [messages, setMessages] = useState<Message[]>([]);
  const [draft, setDraft] = useState("");
  const [sending, setSending] = useState(false);
  const [recording, setRecording] = useState(false);
  const [audioSource, setAudioSource] = useState<string | null>(null);
  const [voiceLatencyMs, setVoiceLatencyMs] = useState<number | null>(null);
  const [pipelineTimings, setPipelineTimings] = useState<PipelineTimings | null>(null);
  const [voiceNotice, setVoiceNotice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const sessionRequested = useRef(false);
  const messagesEnd = useRef<HTMLDivElement>(null);
  const mediaRecorder = useRef<MediaRecorder | null>(null);
  const mediaStream = useRef<MediaStream | null>(null);
  const audioChunks = useRef<Blob[]>([]);
  const unmounted = useRef(false);
  const speechEndedAt = useRef<number | null>(null);
  const responseAudio = useRef<HTMLAudioElement>(null);

  const createSession = useCallback(() => {
    setSessionLoading(true);
    setError(null);

    if (!API_URL) {
      setError("Falta configurar NEXT_PUBLIC_API_URL.");
      setSessionLoading(false);
      return;
    }

    const storedIdentityId = window.localStorage.getItem(IDENTITY_STORAGE_KEY);
    const nextIdentityId = storedIdentityId ?? crypto.randomUUID();
    if (!storedIdentityId) {
      window.localStorage.setItem(IDENTITY_STORAGE_KEY, nextIdentityId);
    }
    setIdentityId(nextIdentityId);
    setConversationId(crypto.randomUUID());
    setSessionLoading(false);
  }, []);

  useEffect(() => {
    if (sessionRequested.current) {
      return;
    }
    sessionRequested.current = true;
    void createSession();
  }, [createSession]);

  useEffect(() => {
    messagesEnd.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, sending]);

  useEffect(() => {
    if (!audioSource || !responseAudio.current) {
      return;
    }
    responseAudio.current.play().catch(() => {
      setError("El navegador bloqueó la reproducción automática. Presioná reproducir para escuchar la respuesta.");
    });
  }, [audioSource]);

  useEffect(() => {
    unmounted.current = false;
    return () => {
      unmounted.current = true;
      mediaRecorder.current?.stop();
      mediaStream.current?.getTracks().forEach((track) => track.stop());
      audioChunks.current = [];
    };
  }, []);

  async function requestMessage(payload: { text?: string; audio_base64?: string }, typedText?: string) {
    if (!identityId || !conversationId) {
      return;
    }

    setSending(true);
    setError(null);
    setAudioSource(null);
    setVoiceLatencyMs(null);
    setPipelineTimings(null);
    setVoiceNotice(null);

    try {
      const response = await fetchWithTimeout("/conversation/message", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ identity_id: identityId, conversation_id: conversationId, ...payload }),
      });
      if (!response.ok) {
        throw new BackendError(await responseError(response));
      }
      const data = (await response.json()) as MessageResponse;
      if (payload.audio_base64) {
        setMessages((current) => [
          ...current,
          { id: crypto.randomUUID(), role: "user", text: data.transcript },
        ]);
      }
      setMessages((current) => [
        ...current,
        { id: crypto.randomUUID(), role: "assistant", text: data.text },
      ]);
      setPipelineTimings(data.timings);
      if (data.audio_base64) {
        setAudioSource(`data:audio/mpeg;base64,${data.audio_base64}`);
      } else {
        speechEndedAt.current = null;
      }
      if (data.audio_error) {
        setVoiceNotice(data.audio_error);
      }
    } catch (requestFailure) {
      if (typedText) {
        setDraft(typedText);
      }
      speechEndedAt.current = null;
      setError(requestFailure instanceof BackendError
        ? requestFailure.message
        : requestError(requestFailure));
    } finally {
      setSending(false);
    }
  }

  async function sendMessage(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const text = draft.trim();
    if (!text || !identityId || !conversationId || sending || recording) {
      return;
    }

    setMessages((current) => [...current, { id: crypto.randomUUID(), role: "user", text }]);
    setDraft("");
    speechEndedAt.current = null;
    await requestMessage({ text }, text);
  }

  async function startRecording() {
    if (!identityId || !conversationId || sending || recording) {
      return;
    }
    if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
      setError("Este navegador no permite grabar audio con MediaRecorder.");
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mimeType = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
        ? "audio/webm;codecs=opus"
        : "audio/webm";
      const recorder = new MediaRecorder(stream, { mimeType });
      mediaStream.current = stream;
      mediaRecorder.current = recorder;
      audioChunks.current = [];
      setError(null);
      setVoiceLatencyMs(null);

      recorder.addEventListener("dataavailable", (event) => {
        if (event.data.size > 0) {
          audioChunks.current.push(event.data);
        }
      });
      recorder.addEventListener("stop", async () => {
        stream.getTracks().forEach((track) => track.stop());
        mediaStream.current = null;
        mediaRecorder.current = null;
        if (unmounted.current) {
          return;
        }
        try {
          const audio = new Blob(audioChunks.current, { type: recorder.mimeType });
          audioChunks.current = [];
          await requestMessage({ audio_base64: await blobToDataUrl(audio) });
        } catch {
          speechEndedAt.current = null;
          setSending(false);
          setError("No se pudo preparar la grabación para enviarla.");
        }
      });
      recorder.start();
      setRecording(true);
    } catch {
      mediaStream.current?.getTracks().forEach((track) => track.stop());
      mediaStream.current = null;
      setError("No se pudo acceder al micrófono. Revisá el permiso del navegador.");
    }
  }

  function stopRecording() {
    if (!mediaRecorder.current || mediaRecorder.current.state !== "recording") {
      return;
    }
    speechEndedAt.current = performance.now();
    setRecording(false);
    setSending(true);
    mediaRecorder.current.stop();
  }

  function registerAudioStart() {
    if (speechEndedAt.current === null) {
      return;
    }
    setVoiceLatencyMs(performance.now() - speechEndedAt.current);
    speechEndedAt.current = null;
  }

  const sessionReady = Boolean(identityId && conversationId);
  const canSend = Boolean(sessionReady && draft.trim() && !sending && !recording);
  const canRecord = Boolean(sessionReady && !sending);

  return (
    <main className="page-shell">
      <section className="chat" aria-label="Chat con Nara">
        <header className="chat-header">
          <div>
            <p className="eyebrow">Compañera virtual</p>
            <h1>Nara</h1>
          </div>
          <span className={`status ${sessionReady ? "status-ready" : ""}`}>
            {sessionLoading ? "Conectando…" : sessionReady ? "Sesión lista" : "Sin conexión"}
          </span>
        </header>

        <div className="messages" aria-live="polite">
          {messages.length === 0 && !sending && (
            <div className="empty-state">
              <h2>Empezá una conversación</h2>
              <p>Nara puede recordar hechos relevantes entre conversaciones.</p>
            </div>
          )}
          {messages.map((message) => (
            <article className={`message message-${message.role}`} key={message.id}>
              <span>{message.role === "user" ? "Vos" : "Nara"}</span>
              <p>{message.text}</p>
            </article>
          ))}
          {sending && (
            <article className="message message-assistant pending">
              <span>Nara</span>
              <p>{recording ? "Escuchando…" : "Pensando y preparando la voz…"}</p>
            </article>
          )}
          <div ref={messagesEnd} />
        </div>

        {(audioSource || pipelineTimings || voiceNotice) && (
          <div className="voice-response">
            {audioSource && (
              <audio ref={responseAudio} controls src={audioSource} onPlaying={registerAudioStart}>
                <track kind="captions" />
              </audio>
            )}
            {voiceNotice && <p className="voice-notice">{voiceNotice}</p>}
            {pipelineTimings && (
              <output className="latency-breakdown">
                <span>STT: {(pipelineTimings.stt_ms / 1000).toFixed(2)} s</span>
                <span>Memoria: {(pipelineTimings.memory_ms / 1000).toFixed(2)} s</span>
                <span>LLM: {(pipelineTimings.llm_ms / 1000).toFixed(2)} s</span>
                <span>TTS: {(pipelineTimings.tts_ms / 1000).toFixed(2)} s</span>
                <span>Backend total: {(pipelineTimings.backend_total_ms / 1000).toFixed(2)} s</span>
                {voiceLatencyMs !== null && (
                  <>
                    <span>Frontend/red/reproducción: {(Math.max(0, voiceLatencyMs - pipelineTimings.backend_total_ms) / 1000).toFixed(2)} s</span>
                    <strong>Latencia de voz: {(voiceLatencyMs / 1000).toFixed(2)} s</strong>
                  </>
                )}
              </output>
            )}
          </div>
        )}

        {error && (
          <div className="error" role="alert">
            <span>{error}</span>
            {!sessionReady && !sessionLoading && (
              <button type="button" onClick={() => createSession()}>Reintentar</button>
            )}
          </div>
        )}

        <form className="composer" onSubmit={sendMessage}>
          <label htmlFor="message">Mensaje</label>
          <div className="composer-row">
            <input
              id="message"
              name="message"
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              placeholder={recording ? "Grabando…" : sessionReady ? "Escribile a Nara…" : "Esperando al backend…"}
              autoComplete="off"
              disabled={!sessionReady || sending || recording}
            />
            <button type="submit" disabled={!canSend}>
              {sending ? "Enviando…" : "Enviar"}
            </button>
            <button
              className={`record-button ${recording ? "record-button-active" : ""}`}
              type="button"
              disabled={!canRecord && !recording}
              onClick={recording ? stopRecording : startRecording}
            >
              {recording ? "Detener" : "Hablar"}
            </button>
          </div>
        </form>
      </section>
    </main>
  );
}
