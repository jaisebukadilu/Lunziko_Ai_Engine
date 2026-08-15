# Lunziko AI Engine — SDK Kotlin

Client Kotlin (JDK 11+, `java.net.http` + kotlinx.serialization) du gateway Lunziko AI Engine.
Convient aussi à Android (JVM).

```kotlin
import com.lunziko.aiengine.LunzikoAIEngine
import com.lunziko.aiengine.ChatMessage

val ai = LunzikoAIEngine("http://localhost:8770", apiKey = "…")

val r = ai.chat(listOf(ChatMessage.user("Explique le rapprochement bancaire")))
println(r["content"])

// Assistant scopé + routage neuronal
val scope = ai.assistantScope("one")
val route = ai.neuralRoute("rédige une note de synthèse")
```

Dépendance unique : `kotlinx-serialization-json` (voir `build.gradle.kts`). Les réponses
sont des `JsonObject` ; méthodes typées pour la conversation, génériques (`get`/`post`) sinon.
