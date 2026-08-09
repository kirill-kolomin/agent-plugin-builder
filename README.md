# agent-plugin-builder

Teach your AI coding agent (Claude Code, Cursor, VS Code, Kiro, or any other [Agent Plugins](https://agent-plugins.org/)-compatible client) how to package skills and MCP servers into a portable plugin that works across all of them — instead of rebuilding the same thing for every tool.

Once installed, just ask your agent things like:

- "Package this as an agent plugin"
- "Turn my MCP server into something Cursor and Claude Code can both load"
- "Validate this plugin against the spec"
- "Add an MCP server to my existing plugin"

and it will scaffold the `plugin.json`, `skills/`, and `mcp.json` for you, following the spec's exact rules — plus catch mistakes with a built-in validator before you ship anything.

## Install

**Using the [skills CLI](https://skills.sh):**

```bash
npx skills add kirill-kolomin/agent-plugin-builder
```

**Using GitHub CLI (Copilot, other `gh skill`-compatible clients):**

```bash
gh skill install kirill-kolomin/agent-plugin-builder
```

**Manually, for any client:** clone or download this repo, then point your client at it the way that client documents for loading local plugins (most read from a plugins/extensions directory or a config file listing plugin paths).

## What it does

Ask your agent to build or fix an agent plugin, and it will:

1. Figure out whether you need a skill, an MCP server, or both
2. Scaffold the correct directory layout (`plugin.json` at the root, `skills/<name>/SKILL.md`, `mcp.json` if needed)
3. Fill in a valid manifest — the right `$schema`, a name that passes the spec's naming rules, and no fields the spec doesn't allow
4. Wire up MCP servers correctly (stdio, Streamable HTTP, or SSE) with safe path handling and no secrets leaking into the config
5. Run a validator against the result and fix anything it flags before handing the plugin back to you

## Validate a plugin yourself

You can also run the checker directly on any plugin — including ones you didn't build with this skill:

```bash
python3 <install-path>/skills/build-agent-plugin/scripts/validate_plugin.py <path-to-plugin>
```

It checks the manifest, skill discovery, and MCP config against the [Agent Plugins Specification v1.0.0](https://agent-plugins.org/specification) and reports every problem it finds. A clean run prints `VALID (0 errors)`.

## License

MIT — see `LICENSE`.
