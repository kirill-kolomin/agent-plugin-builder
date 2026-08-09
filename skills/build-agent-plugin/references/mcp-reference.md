# `mcp.json` reference (Agent Plugins v1.0.0, §7.2 and §9)

`mcp.json` lives at the plugin root, is never inline in `plugin.json`, and MUST be a JSON object with exactly two top-level fields: `$schema` and `mcpServers`.

- `$schema` MUST be `https://agent-plugins.org/schemas/1.0.0/mcp.schema.json` and MUST match the Agent Plugins version declared by `plugin.json`'s `$schema`. A mismatch invalidates the whole MCP config (not the rest of the plugin).
- `mcpServers` is an object; each key is a server name, each value is one server config. An empty `mcpServers` object is valid.

Each server config has a `type` selecting one of three **closed** variants — fields from another variant, or an unrecognized `type`, make that one server entry invalid (other servers and other component types keep loading).

## `stdio`

| Field | Type | Required | Notes |
|---|---|---|---|
| `type` | `"stdio"` | yes | |
| `command` | string | yes | ONE executable token — a bare name or a `./`-relative path. Never a shell command string. |
| `args` | string[] | no | |
| `env` | object of strings | no | Must NOT contain keys named `PLUGIN_ROOT` or `PLUGIN_DATA` — reserved, client sets these itself |
| `cwd` | string | no | Defaults to plugin root if omitted |

`command` resolution:
- Bare name → resolved via platform executable search (client-defined; plugins must not depend on `PATH` specifically).
- `./`-relative → resolved against plugin root, must stay inside it.
- A plugin that **bundles** its own executable MUST use the `./`-relative form, not rely on `PATH`.
- No placeholder expansion happens in `command` itself.

`cwd` accepted forms (after placeholder expansion, must resolve within the right root):
1. `./`-relative path (plugin root)
2. `${PLUGIN_ROOT}` or `${PLUGIN_ROOT}/...`
3. `${PLUGIN_DATA}` or `${PLUGIN_DATA}/...`

Any other `cwd` form, or one that escapes its root after expansion, invalidates that server entry.

`args` elements and `env` values support `${PLUGIN_ROOT}` / `${PLUGIN_DATA}` expansion (single, non-recursive, exact-occurrence replacement — text introduced by a replacement is never re-scanned). `env` *keys* and `command` do not get expanded.

## `streamable-http` / `sse`

| Field | Type | Required | Notes |
|---|---|---|---|
| `type` | `"streamable-http"` or `"sse"` | yes | `sse` = deprecated legacy HTTP+SSE transport, optional for clients to support |
| `url` | string | yes | Absolute HTTP(S) URL, no userinfo, no fragment |
| `headers` | object of strings | no | Fixed headers only — no placeholder/env expansion |

Rules:
- Non-loopback `url` MUST be HTTPS. Plain HTTP only allowed for `localhost` or a loopback IP literal.
- Header names are case-insensitive; the same name repeated under different casing is invalid.
- **Never put secrets in `headers` or `env`** — both are visible package data, not a credentials mechanism. OAuth / credential storage is entirely client-managed and outside this spec; an auth failure is a connection failure, not an invalid-config error.
- Client-generated auth/protocol headers always win over configured headers with the same name.
- A client must never forward configured headers to a different origin via redirect or a legacy SSE event without explicit user authorization.

## Transport support expectations for clients

A conformant client supports at least one of `stdio` / `streamable-http` (SHOULD support both); `sse` support is optional. Whatever `type` a server declares is what the client attempts first — the spec defines no fallback chain.

## Subprocess environment (§9.1) — what a client guarantees a `stdio` server

- `PLUGIN_ROOT`: absolute path to the resolved plugin root.
- `PLUGIN_DATA`: absolute path to a client-managed, persistent, writable directory dedicated to this installed plugin instance (survives updates, may be deleted on uninstall).
- Use `PLUGIN_ROOT` for bundled scripts/binaries/config; use `PLUGIN_DATA` for anything generated at runtime (installed deps, caches, generated code).
- Configured `env` entries overlay the base environment first; then the client sets `PLUGIN_ROOT`/`PLUGIN_DATA`, overriding anything with those names.
- Don't depend on any other ambient/base-environment variable unless the spec requires it or your own `env` block supplies it.

## Full example

```json
{
  "$schema": "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json",
  "mcpServers": {
    "local-validator": {
      "type": "stdio",
      "command": "./bin/validator",
      "args": ["--data", "${PLUGIN_DATA}/validator"],
      "env": {
        "CONFIG": "${PLUGIN_ROOT}/config.json"
      },
      "cwd": "${PLUGIN_ROOT}"
    },
    "deployment-api": {
      "type": "streamable-http",
      "url": "https://deploy.example.com/mcp",
      "headers": {
        "X-Tenant": "public-tenant"
      }
    },
    "legacy-events": {
      "type": "sse",
      "url": "https://legacy.example.com/sse"
    }
  }
}
```

## Common mistakes

1. Putting a shell string (`"npm run server"`) in `command` instead of one token plus separate `args`.
2. Using `${PLUGIN_ROOT}` inside `command` — expansion doesn't apply there; use a literal `./`-relative path instead.
3. Relying on a bare command name for a bundled executable instead of a `./`-relative path.
4. Putting an API key or token directly in `headers` or `env`.
5. Using plain `http://` for a non-loopback `url`.
6. Letting `mcp.json`'s `$schema` version drift from `plugin.json`'s — silently invalidates the whole MCP config.
7. Adding a `PLUGIN_ROOT`/`PLUGIN_DATA` key inside `env` — reserved names, invalidates the server entry.
