// SDK client Swift de Lunziko AI Engine — autonome, indépendant de Platform.
// URLSession async/await ; macOS 12+/iOS 15+.
//
//   let ai = LunzikoAIEngine(baseURL: "http://localhost:8770", apiKey: "...")
//   let r = try await ai.chat([.user("Bonjour")])
//   print(r["content"] ?? "")

import Foundation
#if canImport(FoundationNetworking)
import FoundationNetworking
#endif

/// Message de conversation.
public struct ChatMessage: Sendable {
    public let role: String
    public let content: String
    public init(role: String, content: String) { self.role = role; self.content = content }
    public static func user(_ c: String) -> ChatMessage { ChatMessage(role: "user", content: c) }
    public static func assistant(_ c: String) -> ChatMessage { ChatMessage(role: "assistant", content: c) }
}

/// Erreur renvoyée par le gateway.
public struct AIEngineError: Error, CustomStringConvertible {
    public let status: Int
    public let detail: String
    public var description: String { "AI Engine \(status): \(detail)" }
}

public final class LunzikoAIEngine {
    private let baseURL: String
    private let apiKey: String?
    private let session: URLSession

    public init(baseURL: String, apiKey: String? = nil, session: URLSession = .shared) {
        self.baseURL = baseURL.hasSuffix("/") ? String(baseURL.dropLast()) : baseURL
        self.apiKey = apiKey
        self.session = session
    }

    private func request(_ method: String, _ path: String, body: [String: Any]? = nil) async throws -> [String: Any] {
        guard let url = URL(string: baseURL + path) else {
            throw AIEngineError(status: 0, detail: "URL invalide")
        }
        var req = URLRequest(url: url)
        req.httpMethod = method
        req.setValue("application/json", forHTTPHeaderField: "content-type")
        if let apiKey { req.setValue(apiKey, forHTTPHeaderField: "X-API-Key") }
        if let body { req.httpBody = try JSONSerialization.data(withJSONObject: body) }
        let (data, response) = try await session.data(for: req)
        let status = (response as? HTTPURLResponse)?.statusCode ?? 0
        if status >= 400 {
            throw AIEngineError(status: status, detail: String(data: data, encoding: .utf8) ?? "")
        }
        if data.isEmpty { return [:] }
        return (try JSONSerialization.jsonObject(with: data) as? [String: Any]) ?? [:]
    }

    /// GET générique (n'importe quel endpoint).
    public func get(_ path: String) async throws -> [String: Any] { try await request("GET", path) }

    /// POST générique.
    public func post(_ path: String, _ body: [String: Any] = [:]) async throws -> [String: Any] {
        try await request("POST", path, body: body)
    }

    // MARK: - Système
    public func health() async throws -> [String: Any] { try await get("/health") }
    public func providers() async throws -> [String: Any] { try await get("/v1/providers") }

    // MARK: - LLM & embeddings
    public func chat(_ messages: [ChatMessage], provider: String? = nil, system: String? = nil,
                     model: String? = nil, maxTokens: Int? = nil) async throws -> [String: Any] {
        var body: [String: Any] = ["messages": messages.map { ["role": $0.role, "content": $0.content] }]
        if let provider { body["provider"] = provider }
        if let system { body["system"] = system }
        if let model { body["model"] = model }
        if let maxTokens { body["max_tokens"] = maxTokens }
        return try await post("/v1/chat", body)
    }

    public func embed(_ texts: [String]) async throws -> [String: Any] {
        try await post("/v1/embed", ["texts": texts])
    }

    // MARK: - RAG
    public func ragSearch(_ namespace: String, _ query: String, k: Int = 5) async throws -> [String: Any] {
        try await post("/v1/rag/search", ["namespace": namespace, "query": query, "k": k])
    }
    public func ragQuery(_ namespace: String, _ query: String, k: Int = 5, provider: String? = nil) async throws -> [String: Any] {
        var body: [String: Any] = ["namespace": namespace, "query": query, "k": k]
        if let provider { body["provider"] = provider }
        return try await post("/v1/rag/query", body)
    }

    // MARK: - Mémoire & knowledge
    public func memorySave(_ userId: String, key: String, value: String, category: String = "general") async throws -> [String: Any] {
        try await post("/v1/memory/save", ["user_id": userId, "key": key, "value": value, "category": category])
    }
    public func memoryRecall(_ userId: String, _ query: String, k: Int = 5) async throws -> [String: Any] {
        try await post("/v1/memory/recall", ["user_id": userId, "query": query, "k": k])
    }
    public func knowledgeSearch(_ org: String, _ query: String, k: Int = 5) async throws -> [String: Any] {
        try await post("/v1/knowledge/search", ["org": org, "query": query, "k": k])
    }

    // MARK: - Agent & outils (A-4b)
    public func agent(_ query: String, userId: String? = nil, org: String? = nil, provider: String? = nil) async throws -> [String: Any] {
        var body: [String: Any] = ["query": query]
        if let userId { body["user_id"] = userId }
        if let org { body["org"] = org }
        if let provider { body["provider"] = provider }
        return try await post("/v1/agent/run", body)
    }
    public func act(_ query: String, tools: [String]? = nil, provider: String? = nil) async throws -> [String: Any] {
        var body: [String: Any] = ["query": query]
        if let tools { body["tools"] = tools }
        if let provider { body["provider"] = provider }
        return try await post("/v1/agent/act", body)
    }
    public func tools() async throws -> [String: Any] { try await get("/v1/tools") }
    public func runTool(_ name: String, arguments: [String: Any]) async throws -> [String: Any] {
        try await post("/v1/tools/run", ["name": name, "arguments": arguments])
    }

    // MARK: - Écosystème
    public func ecosystemApps() async throws -> [String: Any] { try await get("/v1/ecosystem/apps") }
    public func ecosystemSearch(_ query: String, k: Int = 5) async throws -> [String: Any] {
        try await post("/v1/ecosystem/search", ["query": query, "k": k])
    }

    // MARK: - Activité & contexte
    public func activityLog(_ userId: String, app: String, action: String, target: String = "",
                            status: String = "ok", detail: String = "") async throws -> [String: Any] {
        try await post("/v1/activity/log", ["user_id": userId, "app": app, "action": action,
                                            "target": target, "status": status, "detail": detail])
    }
    public func contextAssemble(_ userId: String, query: String = "", app: String? = nil) async throws -> [String: Any] {
        var body: [String: Any] = ["user_id": userId, "query": query]
        if let app { body["app"] = app }
        return try await post("/v1/context/assemble", body)
    }

    // MARK: - Assistant scopé & handoff
    public func assistantAsk(_ app: String, _ query: String, userId: String? = nil) async throws -> [String: Any] {
        var body: [String: Any] = ["query": query]
        if let userId { body["user_id"] = userId }
        return try await post("/v1/assistant/\(app)/ask", body)
    }
    public func assistantScope(_ app: String) async throws -> [String: Any] { try await get("/v1/assistant/\(app)/scope") }
    public func handoffOpenWith(_ fromApp: String, filename: String) async throws -> [String: Any] {
        try await post("/v1/handoff/open-with", ["from_app": fromApp, "filename": filename])
    }

    // MARK: - Neural & données
    public func neuralRoute(_ query: String) async throws -> [String: Any] {
        try await post("/v1/neural/route", ["query": query])
    }
    public func mlPredict(_ name: String, text: String) async throws -> [String: Any] {
        try await post("/v1/neural/ml/predict", ["name": name, "text": text])
    }
    public func dataCleanText(_ texts: [String], minLen: Int = 1) async throws -> [String: Any] {
        try await post("/v1/data/clean-text", ["texts": texts, "min_len": minLen])
    }

    // MARK: - Automatisation (A-10)
    public func runFlow(_ name: String, input: [String: Any]) async throws -> [String: Any] {
        try await post("/v1/automation/flows/\(name)/run", ["input": input])
    }
}
