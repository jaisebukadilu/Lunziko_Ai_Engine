/**
 * SDK client de Lunziko AI Engine — autonome, indépendant de Platform.
 * Un seul client fetch pour tout le gateway `/v1/*`. Node 18+ ou navigateur.
 *
 *   const ai = new LunzikoAIEngine({ baseUrl: "http://localhost:8770", apiKey: "..." });
 *   const r = await ai.chat({ messages: [{ role: "user", content: "Bonjour" }] });
 */

export interface ClientOptions {
  baseUrl: string;
  apiKey?: string;
  fetch?: typeof fetch;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface ChatResult {
  content: string;
  provider: string;
  model: string;
  input_tokens: number;
  output_tokens: number;
}

export interface ChatRequest {
  messages: ChatMessage[];
  provider?: string;
  system?: string;
  model?: string;
  max_tokens?: number;
}

export interface EmbedResult {
  vectors: number[][];
  provider: string;
  model: string;
  dim: number;
}

export interface RagHit {
  id: string;
  score: number;
  text: string;
  meta: Record<string, unknown>;
}

export class LunzikoAIEngine {
  private readonly baseUrl: string;
  private readonly apiKey?: string;
  private readonly _fetch: typeof fetch;

  constructor(opts: ClientOptions) {
    this.baseUrl = opts.baseUrl.replace(/\/$/, "");
    this.apiKey = opts.apiKey;
    this._fetch = opts.fetch ?? fetch;
  }

  private async request<T>(method: string, path: string, body?: unknown): Promise<T> {
    const headers: Record<string, string> = { "content-type": "application/json" };
    if (this.apiKey) headers["X-API-Key"] = this.apiKey;
    const res = await this._fetch(`${this.baseUrl}${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    if (!res.ok) {
      const detail = await res.text();
      throw new Error(`AI Engine ${res.status}: ${detail}`);
    }
    return (await res.json()) as T;
  }

  // --- Système ---
  health() {
    return this.request<Record<string, unknown>>("GET", "/health");
  }
  providers() {
    return this.request<{ available: string[] }>("GET", "/v1/providers");
  }

  // --- LLM & embeddings ---
  chat(req: ChatRequest) {
    return this.request<ChatResult>("POST", "/v1/chat", req);
  }
  embed(texts: string[]) {
    return this.request<EmbedResult>("POST", "/v1/embed", { texts });
  }

  // --- RAG ---
  rag = {
    index: (namespace: string, id: string, text: string, meta?: Record<string, unknown>) =>
      this.request<{ chunks_indexed: number }>("POST", "/v1/rag/index", { namespace, id, text, meta }),
    search: (namespace: string, query: string, k = 5) =>
      this.request<{ results: RagHit[] }>("POST", "/v1/rag/search", { namespace, query, k }),
    query: (namespace: string, query: string, opts: { k?: number; provider?: string } = {}) =>
      this.request<{ answer: ChatResult; sources: RagHit[] }>("POST", "/v1/rag/query", {
        namespace,
        query,
        ...opts,
      }),
  };

  // --- Mémoire ---
  memory = {
    save: (user_id: string, key: string, value: string, category = "general") =>
      this.request<{ id: string }>("POST", "/v1/memory/save", { user_id, key, value, category }),
    list: (user_id: string) =>
      this.request<{ items: unknown[] }>("GET", `/v1/memory/list?user_id=${encodeURIComponent(user_id)}`),
    recall: (user_id: string, query: string, k = 5) =>
      this.request<{ items: unknown[] }>("POST", "/v1/memory/recall", { user_id, query, k }),
  };

  // --- Knowledge ---
  knowledge = {
    add: (org: string, type: string, title: string, content = "", tags: string[] = []) =>
      this.request<{ id: string; auto_links: unknown[] }>("POST", "/v1/knowledge/add", {
        org,
        type,
        title,
        content,
        tags,
      }),
    search: (org: string, query: string, k = 5) =>
      this.request<{ results: unknown[] }>("POST", "/v1/knowledge/search", { org, query, k }),
  };

  // --- Agent ---
  agent(query: string, opts: { agent?: string; user_id?: string; org?: string; provider?: string; save_memory?: boolean } = {}) {
    return this.request<{ capability: string; answer: ChatResult; used: Record<string, number> }>(
      "POST",
      "/v1/agent/run",
      { query, ...opts },
    );
  }

  // --- Workflows ---
  workflow = {
    types: () => this.request<{ types: string[] }>("GET", "/v1/workflow/types"),
    run: (type: string, inputs: Record<string, unknown>) =>
      this.request<Record<string, unknown>>("POST", "/v1/workflow/run", { type, inputs }),
  };

  // --- Voix (TTS/STT/MT : 501 jusqu'aux phases V-1→V-3) ---
  voice = {
    voices: () => this.request<unknown[]>("GET", "/v1/voice/voices"),
    packs: () => this.request<unknown[]>("GET", "/v1/voice/packs"),
    tts: (text: string, voice: string, lang: string) =>
      this.request<unknown>("POST", "/v1/voice/tts", { text, voice, lang }),
  };
}

export default LunzikoAIEngine;
