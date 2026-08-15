/// SDK client de Lunziko AI Engine — autonome, indépendant de Platform.
///
/// Un seul client pour tout le gateway `/v1/*`.
///
///     final ai = LunzikoAIEngine(baseUrl: 'http://localhost:8770', apiKey: '...');
///     final r = await ai.chat([ChatMessage.user('Bonjour')]);
///     print(r['content']);
library lunziko_ai_engine;

import 'dart:convert';
import 'package:http/http.dart' as http;

/// Message de conversation.
class ChatMessage {
  final String role;
  final String content;
  ChatMessage(this.role, this.content);
  factory ChatMessage.user(String content) => ChatMessage('user', content);
  factory ChatMessage.assistant(String content) => ChatMessage('assistant', content);
  Map<String, dynamic> toJson() => {'role': role, 'content': content};
}

/// Erreur renvoyée par le gateway.
class AIEngineException implements Exception {
  final int status;
  final String detail;
  AIEngineException(this.status, this.detail);
  @override
  String toString() => 'AI Engine $status: $detail';
}

class LunzikoAIEngine {
  final String baseUrl;
  final String? apiKey;
  final http.Client _client;

  LunzikoAIEngine({required String baseUrl, this.apiKey, http.Client? client})
      : baseUrl = baseUrl.replaceAll(RegExp(r'/+$'), ''),
        _client = client ?? http.Client();

  Future<dynamic> _request(String method, String path, [Object? body]) async {
    final headers = {'content-type': 'application/json'};
    if (apiKey != null) headers['X-API-Key'] = apiKey!;
    final uri = Uri.parse('$baseUrl$path');
    final encoded = body == null ? null : jsonEncode(body);
    late http.Response res;
    switch (method) {
      case 'GET':
        res = await _client.get(uri, headers: headers);
        break;
      case 'PUT':
        res = await _client.put(uri, headers: headers, body: encoded);
        break;
      case 'DELETE':
        res = await _client.delete(uri, headers: headers);
        break;
      default:
        res = await _client.post(uri, headers: headers, body: encoded);
    }
    if (res.statusCode >= 400) {
      throw AIEngineException(res.statusCode, res.body);
    }
    return res.body.isEmpty ? null : jsonDecode(res.body);
  }

  /// GET générique (n'importe quel endpoint du gateway).
  Future<Map<String, dynamic>> get(String path) async =>
      (await _request('GET', path)) as Map<String, dynamic>;

  /// POST générique.
  Future<Map<String, dynamic>> post(String path, [Object body = const {}]) async =>
      (await _request('POST', path, body)) as Map<String, dynamic>;

  void close() => _client.close();

  // --- Système ---
  Future<Map<String, dynamic>> health() => get('/health');
  Future<Map<String, dynamic>> providers() => get('/v1/providers');

  // --- LLM & embeddings ---
  Future<Map<String, dynamic>> chat(List<ChatMessage> messages,
          {String? provider, String? system, String? model, int? maxTokens}) =>
      post('/v1/chat', {
        'messages': messages.map((m) => m.toJson()).toList(),
        if (provider != null) 'provider': provider,
        if (system != null) 'system': system,
        if (model != null) 'model': model,
        if (maxTokens != null) 'max_tokens': maxTokens,
      });

  Future<Map<String, dynamic>> embed(List<String> texts) => post('/v1/embed', {'texts': texts});

  // --- RAG ---
  Future<Map<String, dynamic>> ragIndex(String namespace, String id, String text,
          {Map<String, dynamic>? meta}) =>
      post('/v1/rag/index', {'namespace': namespace, 'id': id, 'text': text, 'meta': meta ?? {}});
  Future<Map<String, dynamic>> ragSearch(String namespace, String query, {int k = 5}) =>
      post('/v1/rag/search', {'namespace': namespace, 'query': query, 'k': k});
  Future<Map<String, dynamic>> ragQuery(String namespace, String query,
          {int k = 5, String? provider}) =>
      post('/v1/rag/query',
          {'namespace': namespace, 'query': query, 'k': k, if (provider != null) 'provider': provider});

  // --- Mémoire & knowledge ---
  Future<Map<String, dynamic>> memorySave(String userId, String key, String value,
          {String category = 'general'}) =>
      post('/v1/memory/save', {'user_id': userId, 'key': key, 'value': value, 'category': category});
  Future<Map<String, dynamic>> memoryRecall(String userId, String query, {int k = 5}) =>
      post('/v1/memory/recall', {'user_id': userId, 'query': query, 'k': k});
  Future<Map<String, dynamic>> knowledgeSearch(String org, String query, {int k = 5}) =>
      post('/v1/knowledge/search', {'org': org, 'query': query, 'k': k});

  // --- Agent & outils (A-4b) ---
  Future<Map<String, dynamic>> agent(String query, {Map<String, dynamic>? options}) =>
      post('/v1/agent/run', {'query': query, ...?options});
  Future<Map<String, dynamic>> act(String query, {List<String>? tools, String? provider}) =>
      post('/v1/agent/act',
          {'query': query, if (tools != null) 'tools': tools, if (provider != null) 'provider': provider});
  Future<Map<String, dynamic>> tools() => get('/v1/tools');
  Future<Map<String, dynamic>> runTool(String name, Map<String, dynamic> arguments) =>
      post('/v1/tools/run', {'name': name, 'arguments': arguments});

  // --- Écosystème ---
  Future<Map<String, dynamic>> ecosystemApps() => get('/v1/ecosystem/apps');
  Future<Map<String, dynamic>> ecosystemSearch(String query, {int k = 5}) =>
      post('/v1/ecosystem/search', {'query': query, 'k': k});

  // --- Activité & contexte ---
  Future<Map<String, dynamic>> activityLog(String userId, String app, String action,
          {String target = '', String status = 'ok', String detail = ''}) =>
      post('/v1/activity/log', {
        'user_id': userId, 'app': app, 'action': action,
        'target': target, 'status': status, 'detail': detail,
      });
  Future<Map<String, dynamic>> contextAssemble(String userId, {String query = '', String? app}) =>
      post('/v1/context/assemble',
          {'user_id': userId, 'query': query, if (app != null) 'app': app});

  // --- Assistant scopé & handoff ---
  Future<Map<String, dynamic>> assistantAsk(String app, String query, {String? userId}) =>
      post('/v1/assistant/$app/ask', {'query': query, if (userId != null) 'user_id': userId});
  Future<Map<String, dynamic>> assistantScope(String app) => get('/v1/assistant/$app/scope');
  Future<Map<String, dynamic>> handoffOpenWith(String fromApp, String filename) =>
      post('/v1/handoff/open-with', {'from_app': fromApp, 'filename': filename});

  // --- Neural (routeur + ML) & données ---
  Future<Map<String, dynamic>> neuralRoute(String query) => post('/v1/neural/route', {'query': query});
  Future<Map<String, dynamic>> mlPredict(String name, String text) =>
      post('/v1/neural/ml/predict', {'name': name, 'text': text});
  Future<Map<String, dynamic>> dataCleanText(List<String> texts, {int minLen = 1}) =>
      post('/v1/data/clean-text', {'texts': texts, 'min_len': minLen});

  // --- Automatisation (A-10) ---
  Future<Map<String, dynamic>> runFlow(String name, Map<String, dynamic> input) =>
      post('/v1/automation/flows/$name/run', {'input': input});
}
