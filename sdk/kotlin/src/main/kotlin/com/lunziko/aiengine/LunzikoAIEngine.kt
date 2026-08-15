/*
 * SDK client Kotlin de Lunziko AI Engine — autonome, indépendant de Platform.
 * JDK 11+ (java.net.http) + kotlinx.serialization.
 *
 *   val ai = LunzikoAIEngine("http://localhost:8770", apiKey = "...")
 *   val r = ai.chat(listOf(ChatMessage.user("Bonjour")))
 *   println(r["content"])
 */
package com.lunziko.aiengine

import java.net.URI
import java.net.http.HttpClient
import java.net.http.HttpRequest
import java.net.http.HttpResponse
import kotlinx.serialization.json.*

/** Erreur renvoyée par le gateway. */
class AIEngineException(val status: Int, val detail: String) :
    RuntimeException("AI Engine $status: $detail")

/** Message de conversation. */
data class ChatMessage(val role: String, val content: String) {
    companion object {
        fun user(content: String) = ChatMessage("user", content)
        fun assistant(content: String) = ChatMessage("assistant", content)
    }
}

class LunzikoAIEngine(
    baseUrl: String,
    private val apiKey: String? = null,
    private val http: HttpClient = HttpClient.newHttpClient(),
) {
    private val baseUrl = baseUrl.trimEnd('/')
    private val json = Json { ignoreUnknownKeys = true }

    private fun request(method: String, path: String, body: JsonElement? = null): JsonObject {
        val builder = HttpRequest.newBuilder(URI.create("$baseUrl$path"))
            .header("content-type", "application/json")
        apiKey?.let { builder.header("X-API-Key", it) }
        val publisher = if (body == null) HttpRequest.BodyPublishers.noBody()
            else HttpRequest.BodyPublishers.ofString(body.toString())
        when (method) {
            "GET" -> builder.GET()
            "PUT" -> builder.PUT(publisher)
            "DELETE" -> builder.DELETE()
            else -> builder.POST(publisher)
        }
        val res = http.send(builder.build(), HttpResponse.BodyHandlers.ofString())
        if (res.statusCode() >= 400) throw AIEngineException(res.statusCode(), res.body())
        val txt = res.body()
        return if (txt.isBlank()) JsonObject(emptyMap()) else json.parseToJsonElement(txt).jsonObject
    }

    /** GET générique (n'importe quel endpoint). */
    fun get(path: String): JsonObject = request("GET", path)

    /** POST générique. */
    fun post(path: String, body: JsonObject = JsonObject(emptyMap())): JsonObject =
        request("POST", path, body)

    // --- Système ---
    fun health(): JsonObject = get("/health")
    fun providers(): JsonObject = get("/v1/providers")

    // --- LLM & embeddings ---
    fun chat(messages: List<ChatMessage>, provider: String? = null, system: String? = null,
             model: String? = null, maxTokens: Int? = null): JsonObject {
        val body = buildJsonObject {
            putJsonArray("messages") {
                messages.forEach { add(buildJsonObject { put("role", it.role); put("content", it.content) }) }
            }
            provider?.let { put("provider", it) }
            system?.let { put("system", it) }
            model?.let { put("model", it) }
            maxTokens?.let { put("max_tokens", it) }
        }
        return post("/v1/chat", body)
    }

    fun embed(texts: List<String>): JsonObject =
        post("/v1/embed", buildJsonObject { putJsonArray("texts") { texts.forEach { add(it) } } })

    // --- RAG ---
    fun ragSearch(namespace: String, query: String, k: Int = 5): JsonObject =
        post("/v1/rag/search", buildJsonObject { put("namespace", namespace); put("query", query); put("k", k) })
    fun ragQuery(namespace: String, query: String, k: Int = 5, provider: String? = null): JsonObject =
        post("/v1/rag/query", buildJsonObject {
            put("namespace", namespace); put("query", query); put("k", k); provider?.let { put("provider", it) }
        })

    // --- Mémoire & knowledge ---
    fun memorySave(userId: String, key: String, value: String, category: String = "general"): JsonObject =
        post("/v1/memory/save", buildJsonObject {
            put("user_id", userId); put("key", key); put("value", value); put("category", category)
        })
    fun memoryRecall(userId: String, query: String, k: Int = 5): JsonObject =
        post("/v1/memory/recall", buildJsonObject { put("user_id", userId); put("query", query); put("k", k) })
    fun knowledgeSearch(org: String, query: String, k: Int = 5): JsonObject =
        post("/v1/knowledge/search", buildJsonObject { put("org", org); put("query", query); put("k", k) })

    // --- Agent & outils (A-4b) ---
    fun agent(query: String, userId: String? = null, org: String? = null, provider: String? = null): JsonObject =
        post("/v1/agent/run", buildJsonObject {
            put("query", query); userId?.let { put("user_id", it) }; org?.let { put("org", it) }
            provider?.let { put("provider", it) }
        })
    fun act(query: String, tools: List<String>? = null, provider: String? = null): JsonObject =
        post("/v1/agent/act", buildJsonObject {
            put("query", query)
            tools?.let { putJsonArray("tools") { it.forEach { t -> add(t) } } }
            provider?.let { put("provider", it) }
        })
    fun tools(): JsonObject = get("/v1/tools")
    fun runTool(name: String, arguments: JsonObject): JsonObject =
        post("/v1/tools/run", buildJsonObject { put("name", name); put("arguments", arguments) })

    // --- Écosystème ---
    fun ecosystemApps(): JsonObject = get("/v1/ecosystem/apps")
    fun ecosystemSearch(query: String, k: Int = 5): JsonObject =
        post("/v1/ecosystem/search", buildJsonObject { put("query", query); put("k", k) })

    // --- Activité & contexte ---
    fun activityLog(userId: String, app: String, action: String, target: String = "",
                    status: String = "ok", detail: String = ""): JsonObject =
        post("/v1/activity/log", buildJsonObject {
            put("user_id", userId); put("app", app); put("action", action)
            put("target", target); put("status", status); put("detail", detail)
        })
    fun contextAssemble(userId: String, query: String = "", app: String? = null): JsonObject =
        post("/v1/context/assemble", buildJsonObject {
            put("user_id", userId); put("query", query); app?.let { put("app", it) }
        })

    // --- Assistant scopé & handoff ---
    fun assistantAsk(app: String, query: String, userId: String? = null): JsonObject =
        post("/v1/assistant/$app/ask", buildJsonObject { put("query", query); userId?.let { put("user_id", it) } })
    fun assistantScope(app: String): JsonObject = get("/v1/assistant/$app/scope")
    fun handoffOpenWith(fromApp: String, filename: String): JsonObject =
        post("/v1/handoff/open-with", buildJsonObject { put("from_app", fromApp); put("filename", filename) })

    // --- Neural & données ---
    fun neuralRoute(query: String): JsonObject =
        post("/v1/neural/route", buildJsonObject { put("query", query) })
    fun mlPredict(name: String, text: String): JsonObject =
        post("/v1/neural/ml/predict", buildJsonObject { put("name", name); put("text", text) })
    fun dataCleanText(texts: List<String>, minLen: Int = 1): JsonObject =
        post("/v1/data/clean-text", buildJsonObject {
            putJsonArray("texts") { texts.forEach { add(it) } }; put("min_len", minLen)
        })

    // --- Automatisation (A-10) ---
    fun runFlow(name: String, input: JsonObject): JsonObject =
        post("/v1/automation/flows/$name/run", buildJsonObject { put("input", input) })
}
