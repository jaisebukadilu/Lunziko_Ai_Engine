# Lunziko AI Engine — SDK Swift

Client Swift (async/await, URLSession) du gateway Lunziko AI Engine. macOS 12+ / iOS 15+.

```swift
import LunzikoAIEngine

let ai = LunzikoAIEngine(baseURL: "http://localhost:8770", apiKey: "…")

let health = try await ai.health()
let r = try await ai.chat([.user("Explique le rapprochement bancaire")])
print(r["content"] as? String ?? "")

// Assistant scopé à une app + handoff
let scope = try await ai.assistantScope("one")
let open = try await ai.handoffOpenWith("one", filename: "budget.xlsx")
```

Ajout via SwiftPM : `.package(path: "…/sdk/swift")` puis produit `LunzikoAIEngine`.

Les réponses sont des `[String: Any]` (JSON) ; méthodes typées pour la conversation
(`ChatMessage`) et génériques (`get`/`post`) pour tout endpoint du gateway.
