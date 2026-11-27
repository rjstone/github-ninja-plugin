# github-ninja

GitHub know-how for coding agents, packaged once and installable in several agent harnesses.
Today it is a bundle of [Agent Skills](https://agentskills.io); commands and other components
may follow.

## Skills

| Skill | What it helps with | Source |
|---|---|---|
| `gh` | Driving the GitHub CLI from an agent: JSON output, pagination, repo targeting, search vs list, `gh api` for REST and GraphQL | [cli/cli](https://github.com/cli/cli/tree/trunk/skills/gh) |
| `github-actions-hardening` | Workflow security: `${{ }}` script injection, `pull_request_target` / `workflow_run`, SHA pinning, least-privilege tokens, OIDC | [github/awesome-copilot](https://github.com/github/awesome-copilot) |
| `github-actions-efficiency` | Cutting CI minutes and cost: caching, concurrency, path filters, matrix trimming | github/awesome-copilot |
| `github-actions-runtime-upgrade-conventions` | Moving actions to supported runtimes (e.g. off Node 20) without changing behaviour | github/awesome-copilot |
| `dependabot` | `dependabot.yml`, grouped and security updates, monorepos, auto-triage | github/awesome-copilot |
| `secret-scanning` | Secret scanning, push protection, custom patterns, alert remediation | github/awesome-copilot |
| `codeql` | CodeQL code scanning through Actions and the CodeQL CLI | github/awesome-copilot |

The skills are copied from their upstream repositories (both MIT, GitHub, Inc.) at the commits
listed in [NOTICE](NOTICE) and in each skill's `metadata.upstream`. Each copied skill folder keeps
its upstream licence as `LICENSE.txt`.

## Install

**Claude Code**

```
/plugin marketplace add rjstone/plugin-marketplace
/plugin install github-ninja@rjstone
```

Or straight from this repository: `/plugin marketplace add rjstone/github-ninja-plugin`, then
`/plugin install github-ninja@github-ninja`.

**skills.sh** (Claude Code, Codex, Cursor, opencode and other agents)

```
npx skills add rjstone/github-ninja-plugin
```

**opencode (HTTP skill catalog)**: add this URL to `skills` in `opencode.json(c)`:

```json
{ "skills": ["https://raw.githubusercontent.com/rjstone/github-ninja-plugin/main/skills/"] }
```

opencode reads `skills/index.json` there and re-downloads a skill when its version changes.

**Codex**: use skills.sh for now. A native Codex manifest will be added if Codex's own plugin
loader needs one.

## Licence

MIT. See [LICENSE](LICENSE), and [NOTICE](NOTICE) for the upstream copyrights.
