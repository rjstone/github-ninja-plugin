---
name: github-mcp-config
description: 'Use only when a skill needs the GitHub MCP tools (create_pull_request, pull_request_read, ...) but no GitHub MCP server is configured in this harness, so you can advise or help the user add GitHub''s official server the best way for their harness and auth.'
metadata:
  version: "0.1.0"
---

# Adding GitHub's official MCP server

The server is [github/github-mcp-server](https://github.com/github/github-mcp-server). Its
per-harness guides are in
[docs/installation-guides](https://github.com/github/github-mcp-server/tree/main/docs/installation-guides);
use them for anything not covered here.

## First: is one already there?

Check the harness's MCP list before adding anything (`claude mcp list`, `codex mcp list`,
Cursor's MCP settings, ...). If any GitHub server exists, even under another name, fix or
enable that one instead of adding a second: two near-identical tool sets confuse the model,
and some harnesses don't resolve duplicates. The old npm `@modelcontextprotocol/server-github`
is deprecated and has different tool names; replace it.

## Pick the form by auth

| | Remote, hosted by GitHub | Local (Docker image or binary) |
|---|---|---|
| OAuth, no token | only Copilot hosts (VS Code, Visual Studio, JetBrains, Xcode, Eclipse) | any harness, on github.com: browser login on first use, token kept in memory |
| Personal access token | every other harness, Claude Code, Codex and Cursor included | any harness (`GITHUB_PERSONAL_ACCESS_TOKEN`, takes precedence over OAuth) |

So: user wants no token and isn't on a Copilot host → local server. Otherwise the remote one
is simplest (nothing to install). GitHub Enterprise Server and `ghe.com` need the local
server and their own OAuth or GitHub App: see the repo's `docs/oauth-login.md`.

## Remote (most harnesses: PAT)

Maximal form; drop the lines you don't need:

```json
{ "mcpServers": { "github": {
    "type": "http",
    "url": "https://api.githubcopilot.com/mcp/",
    "headers": {
      "Authorization": "Bearer ${GITHUB_PERSONAL_ACCESS_TOKEN}",
      "X-MCP-Toolsets": "repos,issues,pull_requests",
      "X-MCP-Readonly": "true"
    } } } }
```

- Copilot hosts: leave out `Authorization`; they sign in with OAuth.
- The token comes from the environment, never written into a file. Variable syntax differs:
  Claude Code `${VAR}`, Cursor `${env:VAR}`, Codex `bearer_token_env_var = "VAR"` in
  `~/.codex/config.toml` (or `codex mcp add github --url https://api.githubcopilot.com/mcp/
  --bearer-token-env-var VAR`).
- `X-MCP-Toolsets`: unknown names are silently ignored. `X-MCP-Tools` (single tools): an
  unknown name stops the server. `X-MCP-Readonly`: read tools only; skills that open or merge
  PRs then can't work. A single toolset also works as a URL path,
  `/mcp/x/<toolset>[/readonly]`.
- PAT: a fine-grained token limited to the repos and permissions the user is comfortable with
  (Contents, Issues, Pull requests). The user creates it; never ask them to paste it to you.

## Local, OAuth without a token (github.com)

Docker (the callback port must be published to loopback):

```json
{ "mcpServers": { "github": {
    "command": "docker",
    "args": ["run", "-i", "--rm", "-p", "127.0.0.1:8085:8085",
             "-e", "GITHUB_OAUTH_CALLBACK_PORT", "-e", "GITHUB_TOOLSETS",
             "ghcr.io/github/github-mcp-server:<release tag>"],
    "env": { "GITHUB_OAUTH_CALLBACK_PORT": "8085", "GITHUB_TOOLSETS": "repos,issues,pull_requests" }
} } }
```

- Pin a release tag from the repo's releases (check it with `docker pull`), not `latest`.
- Native binary instead of Docker: `"command": "github-mcp-server", "args": ["stdio"]`, no
  fixed port needed. Headless machines fall back to a device code. See `docs/oauth-login.md`.
- Same switches as env vars: `GITHUB_TOOLSETS`, `GITHUB_TOOLS`, `GITHUB_READ_ONLY=1`.

## Then

- Name the server `github`: skills and docs refer to its tools that way.
- Tell the user which file you would change and show the snippet before writing it; adding an
  MCP server is their decision.
- Verify: the harness lists the server as connected, and a read tool such as `get_me` works.
