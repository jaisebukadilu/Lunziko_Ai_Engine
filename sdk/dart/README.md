# Lunziko AI Engine — SDK Dart

Client Dart/Flutter (package:http) du gateway Lunziko AI Engine.

```dart
import 'package:lunziko_ai_engine/lunziko_ai_engine.dart';

final ai = LunzikoAIEngine(baseUrl: 'http://localhost:8770', apiKey: '…');

final r = await ai.chat([ChatMessage.user('Explique le rapprochement bancaire')]);
print(r['content']);

// Écosystème + automatisation
final apps = await ai.ecosystemSearch('tableaux de bord KPI');
final run = await ai.runFlow('clean_then_search', {'texts': ['a', 'a'], 'query': 'finance'});

ai.close();
```

Dépendance unique : `http` (voir `pubspec.yaml`). Les réponses sont des `Map<String, dynamic>`
(JSON) ; méthodes typées pour la conversation (`ChatMessage`) et génériques (`get`/`post`) sinon.
