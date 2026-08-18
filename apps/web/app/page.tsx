"use client";

import { FormEvent, useCallback, useEffect, useRef, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL;
const REQUEST_TIMEOUT_MS = 45_000;

type Message = {
  id: string;
  role: "user" | "assistant";
  text: string;
};

type SessionResponse = {
  session_id: string;
};

type MessageResponse = {
  text: string;
};

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

export default function Home() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [sessionLoading, setSessionLoading] = useState(true);
  const [messages, setMessages] = useState<Message[]>([]);
  const [draft, setDraft] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const sessionRequested = useRef(false);
  const messagesEnd = useRef<HTMLDivElement>(null);

  const createSession = useCallback(async () => {
    setSessionLoading(true);
    setError(null);

    if (!API_URL) {
      setError("Falta configurar NEXT_PUBLIC_API_URL.");
      setSessionLoading(false);
      return;
    }

    try {
      const response = await fetchWithTimeout("/session", { method: "POST" });
      if (!response.ok) {
        throw new BackendError(await responseError(response));
      }
      const data = (await response.json()) as SessionResponse;
      setSessionId(data.session_id);
    } catch (requestFailure) {
      setError(requestFailure instanceof BackendError
        ? requestFailure.message
        : requestError(requestFailure));
    } finally {
      setSessionLoading(false);
    }
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

  async function sendMessage(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const text = draft.trim();
    if (!text || !sessionId || sending) {
      return;
    }

    setMessages((current) => [...current, { id: crypto.randomUUID(), role: "user", text }]);
    setDraft("");
    setSending(true);
    setError(null);

    try {
      const response = await fetchWithTimeout("/conversation/message", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, text }),
      });
      if (!response.ok) {
        throw new BackendError(await responseError(response));
      }
      const data = (await response.json()) as MessageResponse;
      setMessages((current) => [
        ...current,
        { id: crypto.randomUUID(), role: "assistant", text: data.text },
      ]);
    } catch (requestFailure) {
      setDraft(text);
      setError(requestFailure instanceof BackendError
        ? requestFailure.message
        : requestError(requestFailure));
    } finally {
      setSending(false);
    }
  }

  const canSend = Boolean(sessionId && draft.trim() && !sending);

  return (
    <main className="page-shell">
      <section className="chat" aria-label="Chat con Nara">
        <header className="chat-header">
          <div>
            <p className="eyebrow">Compañera virtual</p>
            <h1>Nara</h1>
          </div>
          <span className={`status ${sessionId ? "status-ready" : ""}`}>
            {sessionLoading ? "Conectando…" : sessionId ? "Sesión lista" : "Sin conexión"}
          </span>
        </header>

        <div className="messages" aria-live="polite">
          {messages.length === 0 && !sending && (
            <div className="empty-state">
              <h2>Empezá una conversación</h2>
              <p>Nara puede recordar hechos relevantes dentro de esta sesión.</p>
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
              <p>Escribiendo…</p>
            </article>
          )}
          <div ref={messagesEnd} />
        </div>

        {error && (
          <div className="error" role="alert">
            <span>{error}</span>
            {!sessionId && !sessionLoading && (
              <button type="button" onClick={() => void createSession()}>Reintentar</button>
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
              placeholder={sessionId ? "Escribile a Nara…" : "Esperando al backend…"}
              autoComplete="off"
              disabled={!sessionId || sending}
            />
            <button type="submit" disabled={!canSend}>
              {sending ? "Enviando…" : "Enviar"}
            </button>
          </div>
        </form>
      </section>
    </main>
  );
}
