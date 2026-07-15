"""Shared, transport-agnostic surface helpers.

Cross-surface presentation primitives (pagination envelopes, serializers) live here so
that every runtime surface — REST, MCP, SSR, WebSocket — depends *down* on `common`
rather than sideways on another surface. Historically these lived under
`runtimes/server/surfaces/rest/`, which forced `mcp -> rest` (and other) sibling
dependencies; 0.47.3 relocated them (T3 de-cycling, root cause "misplaced shared modules").

Add new cross-surface helpers here, not under a single surface.
"""
