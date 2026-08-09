---
name: build-agent-plugin
description: Design, scaffold, and validate Agent Plugins conforming to the Agent Plugins Specification v1.0.0 (agent-plugins.org) — the open, vendor-neutral package format for portable Agent Skills and MCP servers backed by Amazon, Cursor, GitHub, Google, Microsoft, OpenAI, and Vercel. Use this skill whenever the user wants to create a plugin.json manifest, package one or more skills and/or MCP servers for cross-client distribution, convert an existing SKILL.md or MCP config into the portable Agent Plugins layout, add a client-specific extension namespace, or validate a plugin directory (or mcp.json) against the spec — even if they just say "make this an agent plugin" or "package this for Claude Code / Cursor / VS Code / Kiro" without naming the standard explicitly.
license: MIT
metadata:
  author: Patrick
  version: "1.0.0"
  spec_version: "1.0.0"
  spec_url: "https://agent-plugins.org/specification"
---

# Build an Agent Plugin

Agent Plugins is a small, closed package format: **a directory with a manifest and optional components in fixed locations.** There is no build step and no archive format — the directory *is* the package. Your job is to produce (or fix) that directory so any conformant client can load it.

This skill packages the full normative rules so you don't have to re-derive them from memory. Read `references/manifest-reference.md` and `references/mcp-reference.md` before writing JSON by hand — the spec is intentionally strict (closed schemas, exact string formats) and small mistakes make a manifest or server entry invalid rather than merely ignored.

## 1. Figure out what the user actually needs

Before scaffolding, work out:

1. **What already exists?** A loose `SKILL.md`, an MCP server config, both, or nothing yet? If the user has an existing skill or MCP config in a client-specific format, your job is to *relocate/reshape* it into the fixed layout below, not rewrite its behavior.
2. **Which component types?** A plugin needs at least one of `skills/` or `mcp.json` — never neither. Most requests are skills-only; add `mcp.json` only if the user actually has server(s) to expose.
3. **Any client-specific behavior?** Hooks, commands, or agent config that only make sense for one client (e.g. Claude Code, Cursor) belong in a reverse-domain extension namespace (§8), never in the portable core. Don't invent one speculatively — only add it if the user names a concrete client behavior they want.

Don't ask more than one clarifying question if you can infer the rest from context (e.g. an uploaded skill folder tells you the component type).

## 2. Scaffold the directory

Minimum valid plugin (skills-only):

```
<plugin-name>/
├── plugin.json
└── skills/
    └── <skill-name>/
        └── SKILL.md
```

Full layout when there's more to package:

```
<plugin-name>/
├── plugin.json
├── skills/
│   └── <skill-name>/
│       ├── SKILL.md
│       ├── scripts/
│       └── references/
├── mcp.json
├── com.example.client/        # only if a client namespace is actually needed
├── LICENSE
└── README.md
```

Component locations are **fixed** — `skills/` and `mcp.json` at the plugin root, nothing configurable in `plugin.json`. Never invent alternate paths, and never let any file resolve outside the plugin root (no `../`, no absolute paths in plugin-relative fields).

## 3. Write `plugin.json`

Required fields: `$schema` (must be exactly `https://agent-plugins.org/schemas/1.0.0/plugin.schema.json`) and `name`.

The schema is **closed** — only `$schema`, `name`, `version`, `description`, `author`, `homepage`, `repository`, `license`, `keywords`, `extensions` are permitted at the top level. Anything else invalidates the manifest for strict clients. Read `references/manifest-reference.md` for the full field table and the `name` character-set rules (lowercase alphanumeric + `-`/`.`, 1–64 chars, alphanumeric start/end, no `--` or `..`) before writing this file — get the name wrong and the whole plugin is rejected.

## 4. Add skills

Each immediate child of `skills/` containing a `SKILL.md` is one skill. `SKILL.md` itself follows the separate [Agent Skills specification](https://agentskills.io/specification), not this one — Agent Plugins only defines *where* to put it. Practical rules that matter here:

- Folder name and frontmatter `name` should match.
- `description` must say both *what it does* and *when to use it* — this is the only thing loaded into context until the skill actually triggers, so make it earn its place.
- Put anything not needed on every load into `scripts/` (executable) or `references/` (read-on-demand docs), not the SKILL.md body.
- Don't nest a second `SKILL.md` deeper than one level down — clients only scan immediate children of `skills/`.

## 5. Add MCP servers (only if needed)

`mcp.json` is a separate top-level file, never inline in `plugin.json`. It needs `$schema` (matching the same spec version as `plugin.json`) and an `mcpServers` object. Each server is one of three closed variants — `stdio`, `streamable-http`, or `sse` — and mixing fields from different variants invalidates that entry. Read `references/mcp-reference.md` before writing this file; the parts most people get wrong are:

- `command` is one executable token (bare name or a `./`-relative path), never a shell string.
- Bundled executables must use a plugin-relative `command` — don't rely on `PATH`.
- `args`, `env` values, and `cwd` may use `${PLUGIN_ROOT}` / `${PLUGIN_DATA}` placeholders; `command` and `env` *keys* may not.
- Remote `url` must be absolute HTTPS unless it's `localhost`/loopback; never put secrets in `headers` or `env` — they're visible package data, not a secrets mechanism.

## 6. Client extensions (only if the user actually asked for one)

If — and only if — the user wants client-specific behavior (a Claude Code hook, a Cursor-only setting, etc.), use a reverse-domain namespace they control or the client documents, e.g. `com.example.client`. It can show up as a key under `plugin.json`'s `extensions` object, a top-level `<namespace>/` directory, or both. Never put client-specific fields anywhere else in `plugin.json` — the core schema is closed specifically so experiments can't leak into it.

## 7. Validate before handing it over

Run the bundled validator against the plugin root:

```bash
python3 scripts/validate_plugin.py <path-to-plugin-root>
```

It checks the manifest schema and name rules, skill discovery, and `mcp.json` (schema, per-server variant rules, path containment, placeholder usage) against the spec, and reports every violation it finds — errors (spec violations that make something invalid/rejected) separately from warnings (non-fatal issues clients must tolerate, like unknown top-level fields). Fix every error before delivering the plugin; a plugin with only warnings is still conformant. If Python isn't available, walk the same checks manually using `references/conformance-checklist.md`.

## 8. Package and hand off

The plugin is just a directory — zip it (or leave it as a folder if the user is committing it to a repo) and present it. Mention how it's typically installed only if the user asks: most Agent Plugins-compatible clients discover plugins from a local path or a git repository; there's no registry defined by the spec itself.

## Reference files

- `references/manifest-reference.md` — full `plugin.json` field table, name constraints, worked examples, common mistakes
- `references/mcp-reference.md` — full `mcp.json` field tables for all three transports, placeholder expansion rules, containment rules
- `references/conformance-checklist.md` — plugin-author checklist (the spec's Appendix A checklist is written for *client* implementers; this one is reordered for people *writing* a plugin)
- `scripts/validate_plugin.py` — structural validator; run it against any plugin directory, including this one
