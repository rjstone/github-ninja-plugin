# TODO

Open work for github-ninja. Done items are removed (the history is in git and `CHANGELOG.md`).

## Coverage gaps (2026-11-27)

GitHub features no skill covers yet, roughly by how often an agent meets them. For each, first
search upstream (github/awesome-copilot, skills.sh) for a skill worth copying; write our own
only if none fits (see AGENTS.md, "Skills written here").

Big gaps (everyday agent work):

Medium gaps (Actions and platform depth):
- [ ] **Writing actions and reusable workflows**: `workflow_call`, composite, JavaScript and
  Docker actions, matrix strategy, Marketplace publishing.
- [ ] **Deployments, environments and OIDC to clouds**: environment secrets and protection
  rules, required reviewers, keyless OIDC to AWS, Azure and GCP.
- [ ] **Packages and the container registry (GHCR)**: publishing images and npm packages with
  `GITHUB_TOKEN`, visibility, linking to a repo.
- [ ] **Artifact attestations and supply-chain metadata**: `actions/attest-build-provenance`,
  `gh attestation verify`, SBOM export, the dependency-review action.
- [ ] **Security advisories**: repository advisories, private vulnerability reporting, CVE
  requests, `SECURITY.md`.

Smaller or niche:
- [ ] **Projects (v2)**: `gh project`, custom fields, automation, GraphQL.
- [ ] **Codespaces and dev containers**: `devcontainer.json`, prebuilds, secrets.
- [ ] **GraphQL API**: pagination, rate-limit cost, when to prefer it over REST (check what
  `gh` already covers).
- [ ] **Discussions, wikis, gists** (low value for agents).
- [ ] **Organization and enterprise administration**: teams, roles, SSO, audit log (risky for
  agents to act on).
- [ ] **Copilot-side features**: coding agent, custom instructions, Copilot code review,
  GitHub Models (overlaps issue #1).

## To decide

- [ ] Bundle more skills from `github/github-mcp-server` that need the GitHub MCP tools
  (`repository-health-review`, `security-alert-triage`, `release-preparation`)? Its three
  pull-request skills are bundled since 2026-11-28 (the user), next to our own `gh`-based
  `pull-requests` skill. See [issue #1](https://github.com/rjstone/github-ninja-plugin/issues/1).

## Decided against

- Our own `pull-requests` (`gh`) and `rulesets` skills (2026-11-28, the user): baseline agents
  without a skill already got PR mechanics (review API with suggestions, `mergeStateStatus`,
  auto-merge, CODEOWNERS order, merge methods), rulesets (full JSON, bypass actors, tag rules,
  stuck "Expected" checks, `rules/branches/<b>`) and merge queues (`merge_group`) right. The
  process side is covered by the copied github-mcp-server pull-request skills. Revisit only if
  agents are seen failing at these.
- Our own releases-and-tags skill (2026-11-28, the user): a baseline agent without a skill
  already got immutable releases (draft, upload, then publish; notes editable, assets and tag
  not), `gh release create --verify-tag`, `GITHUB_TOKEN`-created releases not starting
  `release: published` workflows, git-cliff `--latest --strip all` notes and a tag-on-main
  check right. Its one miss, unpinned actions, is covered by `github-actions-hardening`.

- `netresearch/github-project-skill@github-project` (branch protection, rulesets, merge
  blockers): partly CC-BY-SA-4.0, whose share-alike terms would complicate the bundle's
  licensing (2026-11-27).
- From awesome-copilot (2026-11-27): `conventional-commit` (superseded by `git-commit`),
  `github-release` (Keep a Changelog flow clashes with git-cliff and tag releases),
  `repo-standardizer` (its CI templates use unpinned actions with no `permissions:`),
  `lean-comments` (not GitHub-specific).

## Packaging

- [ ] opencode plugin package under `opencode/`, if the HTTP skill catalog isn't enough.
- [ ] Codex manifest under `codex/`, only if Codex stops reading `.claude-plugin/plugin.json`.
