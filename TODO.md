# TODO

Open work for github-ninja. Done items are removed (the history is in git and `CHANGELOG.md`).

## Coverage gaps (2026-11-27)

GitHub features no skill covers yet, roughly by how often an agent meets them. For each, first
search upstream (github/awesome-copilot, skills.sh) for a skill worth copying; write our own
only if none fits (see AGENTS.md, "Skills written here").

Big gaps (everyday agent work):
- [ ] **Pull requests and code review**: reviews and inline comments, suggested changes, draft
  and ready, auto-merge, merge methods, merge queue, `CODEOWNERS`.
- [ ] **Rulesets and branch protection**: required checks and reviews, bypass lists, tag
  protection, why a merge is blocked. (`netresearch` github-project was rejected for its
  licence, not its topic.)
- [ ] **Releases and tags**: `gh release`, generated notes, assets, immutable releases,
  release-triggered workflows. Build on git-cliff (awesome-copilot `github-release` clashes).

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
- [ ] **Codespaces and dev containers**: efficiency is covered by the copied
  `github-codespaces-efficiency`; writing a `devcontainer.json` from scratch and Codespaces
  secrets are not.
- [ ] **GraphQL API**: pagination, rate-limit cost, when to prefer it over REST (check what
  `gh` already covers).
- [ ] **Discussions, wikis, gists** (low value for agents).
- [ ] **Organization and enterprise administration**: teams, roles, SSO, audit log (risky for
  agents to act on).
- [ ] **Copilot-side features**: coding agent, custom instructions, Copilot code review,
  GitHub Models (overlaps issue #1).

## To decide

- [ ] Bundle skills from `github/github-mcp-server` that need the GitHub MCP tools
  (`repository-health-review`, `security-alert-triage`, `release-preparation`)?
  See [issue #1](https://github.com/rjstone/github-ninja-plugin/issues/1).

## Decided against

- `netresearch/github-project-skill@github-project` (branch protection, rulesets, merge
  blockers): partly CC-BY-SA-4.0, whose share-alike terms would complicate the bundle's
  licensing (2026-11-27).
- From awesome-copilot (2026-11-27): `conventional-commit` (superseded by `git-commit`),
  `github-release` (Keep a Changelog flow clashes with git-cliff and tag releases),
  `repo-standardizer` (its CI templates use unpinned actions with no `permissions:`),
  `lean-comments` (not GitHub-specific).
- From a skills.sh search (`npx skills find`, 2026-11-28) for the medium gaps:
  `wshobson/agents@github-actions-templates` (MIT, 18.7K installs: 19 unpinned actions, almost
  no `permissions:`), `trailofbits/skills@devcontainer-setup` (CC-BY-SA-4.0, the same
  share-alike problem as `netresearch`), `github/awesome-copilot@gh-cli` (overlaps the bundled
  `gh` skill). Nothing reputable found for OIDC, environments, GHCR, attestations,
  advisories, Projects v2 or GraphQL. `github-codespaces-efficiency` was copied.

## Packaging

- [ ] opencode plugin package under `opencode/`, if the HTTP skill catalog isn't enough.
- [ ] Codex manifest under `codex/`, only if Codex stops reading `.claude-plugin/plugin.json`.
