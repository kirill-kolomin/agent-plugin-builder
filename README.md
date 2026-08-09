# agent-plugin-builder

An [Agent Plugin](https://agent-plugins.org/) (spec v1.0.0) containing one skill, `build-agent-plugin`, that teaches an agent how to design, scaffold, and validate other Agent Plugins.

This package is itself a conformant plugin — it's the reference example as much as it is the tool.

```
agent-plugin-builder/
├── plugin.json                      # required manifest
├── LICENSE
├── README.md
└── skills/
    └── build-agent-plugin/
        ├── SKILL.md                 # the skill an agent loads
        ├── scripts/
        │   └── validate_plugin.py   # structural validator, usable on ANY plugin
        └── references/
            ├── manifest-reference.md
            ├── mcp-reference.md
            └── conformance-checklist.md
```

## Install

Any Agent Plugins-compatible client can load this from a local path or a git checkout — there's no registry defined by the spec itself. For example, with the [skills CLI](https://skills.sh):

```bash
npx skills add <path-or-repo> --skill build-agent-plugin
```

Or point your client (Claude Code, Cursor, VS Code, Kiro, etc.) at this directory directly, per that client's own plugin-loading docs.

## Validate any plugin (including this one)

```bash
python3 skills/build-agent-plugin/scripts/validate_plugin.py <path-to-any-plugin-root>
```

Checks `plugin.json`, `skills/` discovery, and `mcp.json` against the normative rules in the [Agent Plugins Specification v1.0.0](https://agent-plugins.org/specification). Exit code `0` means zero errors (warnings are non-fatal by design).

## License

MIT — see `LICENSE`.
