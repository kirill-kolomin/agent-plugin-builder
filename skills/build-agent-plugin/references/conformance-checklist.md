# Plugin-author conformance checklist

The spec's own Appendix A checklist is written for people *implementing a client loader*. This is the same rules, reordered for someone *building a plugin*. When the two disagree, the normative spec text wins.

## Directory and manifest

- [ ] `plugin.json` exists at the plugin root (not nested)
- [ ] `$schema` is exactly `https://agent-plugins.org/schemas/1.0.0/plugin.schema.json`
- [ ] `name` passes the character-set, length, and start/end rules (§5.5)
- [ ] No top-level fields outside the closed set (`$schema`, `name`, `version`, `description`, `author`, `homepage`, `repository`, `license`, `keywords`, `extensions`)
- [ ] `author`, if present, only has `name`/`email`/`url` sub-fields
- [ ] `extensions`, if present, is an object keyed by reverse-domain namespaces, values are objects
- [ ] No file the plugin references resolves outside the plugin root (no `../`, no absolute paths in plugin-relative fields)

## Skills (if used)

- [ ] Skills live directly under `skills/<skill-name>/SKILL.md` - one directory level, no deeper nesting scanned
- [ ] Each `SKILL.md` conforms to the Agent Skills specification (agentskills.io) - valid frontmatter, `name` matches folder
- [ ] `description` states both what the skill does and when to use it
- [ ] Nothing required for every invocation is buried in `scripts/`/`references/` only - and nothing rarely-needed bloats the SKILL.md body instead of living there

## MCP servers (if used)

- [ ] `mcp.json` is a separate root file, never inline in `plugin.json`
- [ ] `mcp.json`'s `$schema` version matches `plugin.json`'s `$schema` version
- [ ] Every server has a `type` and only the fields valid for that variant
- [ ] `stdio` servers: `command` is a single token (bare name or `./`-relative, never a shell string); bundled executables use the `./`-relative form
- [ ] `stdio` servers: `cwd` (if set) is `./`-relative, `${PLUGIN_ROOT}[...]`, or `${PLUGIN_DATA}[...]` - nothing else
- [ ] `stdio` servers: `env` has no `PLUGIN_ROOT`/`PLUGIN_DATA` keys
- [ ] `streamable-http`/`sse` servers: `url` is absolute HTTP(S), HTTPS unless loopback, no userinfo/fragment
- [ ] No secrets embedded in `headers` or `env` anywhere
- [ ] If the plugin is meant to supply portable components, at least one of `skills/` or `mcp.json` is present. The specification permits a plugin with neither, but it supplies no portable components.

## Client extensions (only if used)

- [ ] Namespace is a reverse-domain string the client documents or the author controls
- [ ] Client-specific manifest data is nested under `extensions.<namespace>`, never at the top level
- [ ] Client-specific files live in a top-level `<namespace>/` directory, not scattered elsewhere

## Before delivery

- [ ] Ran `scripts/validate_plugin.py <plugin-root>` (or walked this checklist manually) with zero errors
- [ ] Warnings, if any, are understood and acceptable (unknown-but-tolerated fields, etc.)
