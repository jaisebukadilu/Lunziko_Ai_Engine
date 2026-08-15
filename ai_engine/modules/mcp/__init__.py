"""Module mcp — Model Context Protocol (A-7) : serveur + client.

Serveur : expose les outils de l'AI Engine (ToolRegistry) via JSON-RPC 2.0 MCP, consommable
par des clients MCP (Claude Desktop, Cline, Continue…). Client : consomme un serveur MCP
externe et importe ses outils dans le registre local. Standard ouvert (MIT), clean-room.
"""

MCP_PROTOCOL_VERSION = "2024-11-05"
