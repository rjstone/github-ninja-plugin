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
| `github-issues` | Creating and managing issues: labels, milestones, issue types and fields, sub-issues and dependencies (GitHub MCP tools or `gh api`) | github/awesome-copilot |
| `diagnose-ci-gate` | "Is this red check mine?": read the real log and first error, classify bug / flaky / environment / pipeline, recommend one action | github/awesome-copilot |
| `git-commit` | Staging and committing (or splitting) changes with Conventional Commits messages, following the repo's own rules; no `--no-verify`, amend or push | github/awesome-copilot |
| `conventional-branch` | Branch names per the Conventional Branch spec (`feature/`, `bugfix/`, agent prefixes such as `claude/`) | github/awesome-copilot |
| `rebase-current-branch` | Safely rebasing the current branch onto the default branch (no auto-stash, no reset, no push) | github/awesome-copilot |
| `npm-trusted-publishing` | npm trusted publishing (OIDC) from Actions instead of `NPM_TOKEN` | github/awesome-copilot |
| `repo-security-posture` | Auditing a repo's security settings and hardening gaps (branch protection, CODEOWNERS, Actions, release integrity, collaborator access, security features), as ranked fixes tied to attack scenarios; its collector script only reads (GitHub API GETs) | [superagent-ai/skills](https://github.com/superagent-ai/skills) |
| `github-pages` | Publishing with GitHub Pages: branch vs Actions source, the pinned deploy workflow, enabling Pages with `gh api`, custom domains, DNS and HTTPS, 404 and base-path troubleshooting | this repo |
| `github-apps` | GitHub Apps: when to use one instead of a PAT or `GITHUB_TOKEN`, creating one, installation tokens in Actions and code (JWT), webhook signature checks, private key rotation | this repo |
| `gh-attach` | Uploading screenshots and files to PRs, issues and comments, and downloading attachments, with the `gh attach` extension | [sudosubin/gh-attach](https://github.com/sudosubin/gh-attach) |

Most skills are copied from their upstream repositories (all MIT; see
[NOTICE](NOTICE)), each pinned to an upstream commit in its `metadata.upstream`. Each copied
skill folder keeps its upstream licence as `LICENSE.txt`. A daily workflow opens (or updates) a
single PR when upstream changes any of them, much like Dependabot; tools a skill installs are
pinned to a release (`skill-pins.json`) and bumped in a separate PR.

**`gh-attach` note:** the skill installs the `gh attach` extension (pinned). For non-image
files, GHES, and as a fallback, that tool reads your browser's GitHub `user_session` cookie (or
`GH_ATTACH_SESSION_TOKEN`), which is a full account credential. Leave the skill unused, or
uninstall the extension, if you don't want that.

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
