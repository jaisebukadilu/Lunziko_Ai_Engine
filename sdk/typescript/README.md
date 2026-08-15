# @lunziko/ai-engine (SDK TypeScript)

Client léger du gateway **Lunziko AI Engine** (autonome). Node 18+ ou navigateur (fetch natif).
Platform, le web et les apps le consomment de la même manière — l'AI Engine reste indépendant.

```bash
npm install   # devDependency: typescript
npm run build # -> dist/
```

## Usage

```ts
import { LunzikoAIEngine } from "@lunziko/ai-engine";

const ai = new LunzikoAIEngine({ baseUrl: "http://localhost:8770", apiKey: process.env.AE_API_KEY });

// Chat (fallback multi-providers côté serveur)
const r = await ai.chat({ messages: [{ role: "user", content: "Explique le RAG" }] });

// RAG
await ai.rag.index("docs", "d1", "Le lingala est une langue bantoue…");
const hits = await ai.rag.search("docs", "quelle langue ?");
const ans = await ai.rag.query("docs", "résume ce que tu sais du lingala");

// Mémoire / Knowledge / Agent / Workflow
await ai.memory.save("u1", "langue", "préfère le lingala", "preferences");
await ai.knowledge.add("acme", "project", "AI Engine", "IA autonome…");
const a = await ai.agent("résume ce rapport", { user_id: "u1", org: "acme" });
const wf = await ai.workflow.run("summarize", { text: "…" });
```

Toutes les méthodes renvoient le JSON du gateway ; les erreurs HTTP lèvent une `Error`.
Voix (`ai.voice.tts/…`) renverra `501` jusqu'aux phases V-1→V-3.

> SDKs Swift / Kotlin / Dart : à venir (même surface d'API).
