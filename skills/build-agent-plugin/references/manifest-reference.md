# `plugin.json` reference (Agent Plugins v1.0.0, §5)

## Required fields

| Field | Type | Rule |
|---|---|---|
| `$schema` | string | MUST be exactly `https://agent-plugins.org/schemas/1.0.0/plugin.schema.json` |
| `name` | string | See name constraints below |

Missing, wrong-typed, or empty required fields make the whole manifest invalid - the client MUST reject the plugin and load none of its components.

## Metadata fields (all optional)

| Field | Type | Notes |
|---|---|---|
| `version` | string | Semantic Versioning RECOMMENDED, not enforced |
| `description` | string | Short purpose statement |
| `author` | object | Only `name`, `email`, `url` string sub-fields permitted - any other sub-field or type is invalid |
| `homepage` | string | Not validated as a real URL by clients |
| `repository` | string | Source repo URL |
| `license` | string | SPDX identifier RECOMMENDED, not enforced |
| `keywords` | string[] | Search/discovery tags |
| `extensions` | object | Client namespaces → objects, see §8 |

Clients must NOT reject a manifest just because `version` isn't valid semver, `homepage`/`repository`/`author.url` isn't a recognized URL, `author.email` isn't a recognized address, or `license` isn't a real SPDX id - but write real values anyway, this is about client tolerance, not an excuse for junk data.

## Closed schema

The **only** permitted top-level keys are: `$schema`, `name`, `version`, `description`, `author`, `homepage`, `repository`, `license`, `keywords`, `extensions`.

- An unknown top-level field is non-fatal - clients report and ignore it, plugin still loads.
- Any other schema violation (wrong type, malformed required field, invalid `author` sub-fields, etc.) is fatal - plugin rejected outright.
- Never put client-specific data at the top level. It belongs under `extensions.<reverse-domain-namespace>`.

## Name constraints (§5.5) - get this wrong and the plugin is rejected

| Constraint | Rule |
|---|---|
| Length | 1–64 characters |
| Character set | `a-z`, `0-9`, `-`, `.` only (lowercase) |
| Start/end | First and last character must be alphanumeric |
| Repetition | No `--` or `..` |

Valid: `my-plugin`, `acme.tools`, `lint3r`, `a`
Invalid: `My-Plugin` (uppercase), `-start` (leading hyphen), `has--double` (consecutive hyphens), `too.many..dots` (consecutive periods), `` (empty)

## Minimal example

```json
{
  "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
  "name": "minimal-plugin"
}
```

## Full example

```json
{
  "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
  "name": "plugin-name",
  "version": "1.2.0",
  "description": "Brief plugin description",
  "author": {
    "name": "Author Name",
    "email": "author@example.com",
    "url": "https://example.com"
  },
  "homepage": "https://docs.example.com/plugin",
  "repository": "https://github.com/example/plugin",
  "license": "MIT",
  "keywords": ["keyword1", "keyword2"],
  "extensions": {
    "com.example.client": {
      "setting": true
    }
  }
}
```

## Path containment (§4.1) - applies to every file the plugin supplies

- Any plugin-relative path field MUST start with `./`, resolve against the plugin root, and stay inside it after resolution. `../` anywhere that escapes the root is invalid.
- Non-path config values (command args, env values) are opaque strings - clients must NOT treat them as paths.
- Symlinks may point within the plugin root; anything resolving outside it is rejected.
- Failure boundary is always the *narrowest* one: a bad manifest path rejects the whole plugin, a bad component location invalidates that component type, a bad individual skill/server entry only skips that entry.

## Common mistakes

1. Using an uppercase or hyphen/period-leading `name` - always lowercase, alphanumeric start/end.
2. Adding a custom top-level field (e.g. `capabilities`, `settings`) instead of nesting it under `extensions`.
3. Declaring components inline in `plugin.json` (`"skills": [...]`) - components are only ever discovered from their fixed filesystem locations (`skills/`, `mcp.json`), never from manifest fields.
4. Forgetting `$schema` or pointing it at the wrong version string.
5. Putting extra fields inside `author` beyond `name`/`email`/`url`.
