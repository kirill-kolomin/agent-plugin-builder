#!/usr/bin/env python3
"""
validate_plugin.py — structural validator for Agent Plugins Specification v1.0.0
(https://agent-plugins.org/specification)

This is a convenience checker, not the official machine-readable schema. It
implements the normative rules from the spec text closely enough to catch the
mistakes plugin authors actually make. When it disagrees with the spec, the
spec wins — see references/manifest-reference.md and references/mcp-reference.md
for the underlying rules, or the spec itself for the final word.

Usage:
    python3 validate_plugin.py <path-to-plugin-root>

Exit code 0 if there are zero errors (warnings are fine). Exit code 1 otherwise.
"""

import json
import os
import re
import sys
import urllib.parse

PLUGIN_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
MCP_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json"

MANIFEST_ALLOWED_TOP = {
    "$schema", "name", "version", "description", "author",
    "homepage", "repository", "license", "keywords", "extensions",
}
AUTHOR_ALLOWED = {"name", "email", "url"}
MCP_ALLOWED_TOP = {"$schema", "mcpServers"}
STDIO_ALLOWED = {"type", "command", "args", "env", "cwd"}
HTTP_ALLOWED = {"type", "url", "headers"}

NAME_RE = re.compile(r"^[a-z0-9]([a-z0-9\-.]*[a-z0-9])?$")
SKILL_NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


class Report:
    def __init__(self):
        self.errors = []
        self.warnings = []

    def error(self, msg):
        self.errors.append(msg)

    def warn(self, msg):
        self.warnings.append(msg)

    def ok(self):
        return not self.errors

    def print(self):
        if self.errors:
            print(f"\n{len(self.errors)} error(s):")
            for e in self.errors:
                print(f"  ERROR   {e}")
        if self.warnings:
            print(f"\n{len(self.warnings)} warning(s):")
            for w in self.warnings:
                print(f"  WARNING {w}")
        if not self.errors and not self.warnings:
            print("\nNo issues found.")
        print()
        print("VALID (0 errors)" if self.ok() else "INVALID (errors present)")


def valid_name(name):
    if not isinstance(name, str) or not (1 <= len(name) <= 64):
        return False
    if "--" in name or ".." in name:
        return False
    return bool(NAME_RE.match(name))


def check_plugin_root(root, r: Report):
    if not os.path.isdir(root):
        r.error(f"plugin root '{root}' is not a directory")
        return None

    manifest_path = os.path.join(root, "plugin.json")
    if not os.path.isfile(manifest_path):
        r.error("plugin.json is missing at the plugin root (required)")
        return None

    try:
        with open(manifest_path, encoding="utf-8") as f:
            manifest = json.load(f)
    except json.JSONDecodeError as e:
        r.error(f"plugin.json is not valid JSON: {e}")
        return None

    if not isinstance(manifest, dict):
        r.error("plugin.json must contain a top-level JSON object")
        return None

    unknown = set(manifest.keys()) - MANIFEST_ALLOWED_TOP
    for k in unknown:
        r.warn(f"plugin.json has unknown top-level field '{k}' (clients report and ignore it, non-fatal)")

    schema = manifest.get("$schema")
    if schema != PLUGIN_SCHEMA:
        r.error(f"plugin.json $schema must be exactly '{PLUGIN_SCHEMA}' (got {schema!r})")

    name = manifest.get("name")
    if name is None:
        r.error("plugin.json is missing required field 'name'")
    elif not valid_name(name):
        r.error(
            f"plugin.json name {name!r} violates naming rules: 1-64 chars, "
            "lowercase alphanumeric/hyphen/period only, alphanumeric start/end, no '--' or '..'"
        )

    for field in ("version", "description", "homepage", "repository", "license"):
        if field in manifest and not isinstance(manifest[field], str):
            r.error(f"plugin.json field '{field}' must be a string (got {type(manifest[field]).__name__})")

    if "keywords" in manifest:
        kw = manifest["keywords"]
        if not isinstance(kw, list) or not all(isinstance(x, str) for x in kw):
            r.error("plugin.json 'keywords' must be an array of strings")

    if "author" in manifest:
        author = manifest["author"]
        if not isinstance(author, dict):
            r.error("plugin.json 'author' must be an object")
        else:
            bad = set(author.keys()) - AUTHOR_ALLOWED
            if bad:
                r.error(f"plugin.json 'author' has disallowed field(s): {sorted(bad)} (only name/email/url permitted)")
            for k, v in author.items():
                if k in AUTHOR_ALLOWED and not isinstance(v, str):
                    r.error(f"plugin.json 'author.{k}' must be a string")

    if "extensions" in manifest:
        ext = manifest["extensions"]
        if not isinstance(ext, dict):
            r.warn("plugin.json 'extensions' is not an object — clients report and ignore it, non-fatal")
        else:
            for ns, val in ext.items():
                if not isinstance(val, dict):
                    r.error(f"plugin.json extensions.{ns!r} must be an object")

    return manifest


def check_skills(root, r: Report):
    skills_dir = os.path.join(root, "skills")
    if not os.path.exists(skills_dir):
        return  # absent is fine, not an error
    if not os.path.isdir(skills_dir):
        r.error("'skills' exists but is not a directory — skills component type is invalid")
        return

    found_any = False
    for entry in sorted(os.listdir(skills_dir)):
        skill_dir = os.path.join(skills_dir, entry)
        if not os.path.isdir(skill_dir):
            continue
        skill_md = os.path.join(skill_dir, "SKILL.md")
        if not os.path.isfile(skill_md):
            continue  # not a discovered skill, silently skipped per spec
        found_any = True
        check_skill_md(entry, skill_md, r)

    if not found_any:
        r.warn("'skills/' exists but no subdirectory contains a SKILL.md — no skills will be discovered")


def check_skill_md(dirname, path, r: Report):
    with open(path, encoding="utf-8") as f:
        text = f.read()

    if not text.startswith("---"):
        r.error(f"skills/{dirname}/SKILL.md must start with YAML frontmatter delimited by '---'")
        return

    parts = text.split("---", 2)
    if len(parts) < 3:
        r.error(f"skills/{dirname}/SKILL.md frontmatter is not properly closed with a second '---'")
        return

    frontmatter = parts[1]
    name_match = re.search(r"^name:\s*(.+)$", frontmatter, re.MULTILINE)
    desc_match = re.search(r"^description:\s*(.+)$", frontmatter, re.MULTILINE)

    if not name_match:
        r.error(f"skills/{dirname}/SKILL.md frontmatter is missing required 'name'")
    else:
        skill_name = name_match.group(1).strip().strip('"\'')
        if skill_name != dirname:
            r.warn(f"skills/{dirname}/SKILL.md name '{skill_name}' does not match its folder name '{dirname}'")
        if not SKILL_NAME_RE.match(skill_name) or len(skill_name) > 64:
            r.warn(f"skills/{dirname}/SKILL.md name '{skill_name}' may violate Agent Skills naming rules")

    if not desc_match:
        r.error(f"skills/{dirname}/SKILL.md frontmatter is missing required 'description'")

    if "<" in frontmatter or ">" in frontmatter:
        r.warn(f"skills/{dirname}/SKILL.md frontmatter contains angle brackets — avoid per Agent Skills spec")


def check_mcp(root, manifest, r: Report):
    mcp_path = os.path.join(root, "mcp.json")
    if not os.path.exists(mcp_path):
        return
    if not os.path.isfile(mcp_path):
        r.error("'mcp.json' exists but is not a regular file — MCP component type is invalid")
        return

    try:
        with open(mcp_path, encoding="utf-8") as f:
            mcp = json.load(f)
    except json.JSONDecodeError as e:
        r.error(f"mcp.json is not valid JSON: {e} — MCP disabled for this plugin")
        return

    if not isinstance(mcp, dict):
        r.error("mcp.json must contain a top-level JSON object")
        return

    unknown = set(mcp.keys()) - MCP_ALLOWED_TOP
    if unknown:
        r.error(f"mcp.json has disallowed top-level field(s): {sorted(unknown)} (only $schema/mcpServers permitted)")

    schema = mcp.get("$schema")
    if schema != MCP_SCHEMA:
        r.error(f"mcp.json $schema must be exactly '{MCP_SCHEMA}' (got {schema!r})")
    elif manifest and manifest.get("$schema") != PLUGIN_SCHEMA:
        r.warn("could not confirm mcp.json version matches plugin.json version (plugin.json invalid)")

    servers = mcp.get("mcpServers")
    if not isinstance(servers, dict):
        r.error("mcp.json 'mcpServers' must be an object")
        return

    for sname, cfg in servers.items():
        check_server(sname, cfg, r)


def check_server(name, cfg, r: Report):
    if not isinstance(cfg, dict):
        r.error(f"mcp.json server '{name}' must be an object")
        return

    stype = cfg.get("type")
    if stype == "stdio":
        check_stdio_server(name, cfg, r)
    elif stype in ("streamable-http", "sse"):
        check_http_server(name, cfg, r)
    else:
        r.error(f"mcp.json server '{name}' has missing or unrecognized 'type' {stype!r} "
                "(must be 'stdio', 'streamable-http', or 'sse')")


def check_stdio_server(name, cfg, r: Report):
    bad = set(cfg.keys()) - STDIO_ALLOWED
    if bad:
        r.error(f"mcp.json server '{name}' (stdio) has field(s) not valid for this variant: {sorted(bad)}")

    command = cfg.get("command")
    if not isinstance(command, str) or not command:
        r.error(f"mcp.json server '{name}' (stdio) is missing required 'command'")
    else:
        if " " in command:
            r.warn(f"mcp.json server '{name}' command {command!r} contains a space — "
                   "'command' must be a single executable token, not a shell string; use 'args' instead")
        if command.startswith(".."):
            r.error(f"mcp.json server '{name}' command {command!r} escapes the plugin root")
        elif "/" in command and not command.startswith("./"):
            r.warn(f"mcp.json server '{name}' command {command!r} looks like a path but doesn't start with './'")

    if "args" in cfg:
        args = cfg["args"]
        if not isinstance(args, list) or not all(isinstance(a, str) for a in args):
            r.error(f"mcp.json server '{name}' 'args' must be an array of strings")

    if "env" in cfg:
        env = cfg["env"]
        if not isinstance(env, dict) or not all(isinstance(v, str) for v in env.values()):
            r.error(f"mcp.json server '{name}' 'env' must be an object of strings")
        else:
            reserved = {"PLUGIN_ROOT", "PLUGIN_DATA"} & set(env.keys())
            if reserved:
                r.error(f"mcp.json server '{name}' 'env' declares reserved key(s) {sorted(reserved)} — "
                        "clients supply these themselves")

    if "cwd" in cfg:
        cwd = cfg["cwd"]
        if not isinstance(cwd, str):
            r.error(f"mcp.json server '{name}' 'cwd' must be a string")
        else:
            valid_forms = (
                cwd.startswith("./")
                or cwd == "${PLUGIN_ROOT}" or cwd.startswith("${PLUGIN_ROOT}/")
                or cwd == "${PLUGIN_DATA}" or cwd.startswith("${PLUGIN_DATA}/")
            )
            if not valid_forms:
                r.error(f"mcp.json server '{name}' 'cwd' {cwd!r} must be './'-relative, "
                        "'${PLUGIN_ROOT}[...]', or '${PLUGIN_DATA}[...]'")


def check_http_server(name, cfg, r: Report):
    bad = set(cfg.keys()) - HTTP_ALLOWED
    if bad:
        r.error(f"mcp.json server '{name}' ({cfg.get('type')}) has field(s) not valid for this variant: {sorted(bad)}")

    url = cfg.get("url")
    if not isinstance(url, str) or not url:
        r.error(f"mcp.json server '{name}' is missing required 'url'")
        return

    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        r.error(f"mcp.json server '{name}' url {url!r} must be an absolute http(s) URL")
        return
    if parsed.username or parsed.password:
        r.error(f"mcp.json server '{name}' url must not contain user info")
    if parsed.fragment:
        r.error(f"mcp.json server '{name}' url must not contain a fragment")

    host = parsed.hostname or ""
    is_loopback = host == "localhost" or host.startswith("127.") or host == "::1"
    if parsed.scheme == "http" and not is_loopback:
        r.error(f"mcp.json server '{name}' url {url!r} uses plain HTTP for a non-loopback host — must be HTTPS")

    if "headers" in cfg:
        headers = cfg["headers"]
        if not isinstance(headers, dict) or not all(isinstance(v, str) for v in headers.values()):
            r.error(f"mcp.json server '{name}' 'headers' must be an object of strings")
        else:
            lower_names = [h.lower() for h in headers]
            if len(lower_names) != len(set(lower_names)):
                r.error(f"mcp.json server '{name}' 'headers' has the same header name repeated under different casing")
            for hv in headers.values():
                if re.search(r"(key|token|secret|password|bearer)", hv, re.IGNORECASE):
                    r.warn(f"mcp.json server '{name}' header value looks like it may contain a secret — "
                           "headers are visible package data, not a credentials mechanism")


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)

    root = sys.argv[1]
    r = Report()
    print(f"Validating Agent Plugin at: {root}")

    manifest = check_plugin_root(root, r)
    if os.path.isdir(root):
        check_skills(root, r)
        check_mcp(root, manifest, r)

        has_skills = os.path.isdir(os.path.join(root, "skills"))
        has_mcp = os.path.isfile(os.path.join(root, "mcp.json"))
        if not has_skills and not has_mcp:
            r.warn("plugin has neither 'skills/' nor 'mcp.json' — it supplies no components to any client")

    r.print()
    sys.exit(0 if r.ok() else 1)


if __name__ == "__main__":
    main()
