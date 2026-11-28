# TODO

Open work for github-ninja. Done items are removed (the history is in git and `CHANGELOG.md`).

## Coverage gaps (2026-11-27)

GitHub features no skill covers yet, roughly by how often an agent meets them. For each, first
search upstream (github/awesome-copilot, skills.sh) for a skill worth copying; write our own
only if none fits (see AGENTS.md, "Skills written here").

Big gaps (everyday agent work): none left. Pull requests are covered by the copied
github-mcp-server skills; rulesets and releases tested fine without a skill (see "Decided
against").

Medium gaps (Actions and platform depth):
- [ ] **Writing actions and reusable workflows**: `workflow_call`, composite, JavaScript and
  Docker actions, matrix strategy, Marketplace publishing. Not covered by a skill:
  awesome-copilot has only an instructions file (`github-actions-ci-cd-best-practices`) and an
  agent (`github-actions-expert`) for *using* Actions; neither covers authoring actions, and
  neither is in skill format.

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

- [ ] Bundle more skills from `github/github-mcp-server` that need the GitHub MCP tools
  (`repository-health-review`, `security-alert-triage`, `release-preparation`)? Its three
  pull-request skills are bundled since 2026-11-28 (the user), next to our own `gh`-based
  `pull-requests` skill. See [issue #1](https://github.com/rjstone/github-ninja-plugin/issues/1).

## Decided against

- Deployments, environments and OIDC to clouds (2026-11-28, the user): too situation-specific.
- Our own GHCR/GitHub Packages, artifact attestations/SBOM and security advisories skills
  (2026-11-28, the user): no upstream skill worth copying (skills.sh: only hits under ~500
  installs or off-topic), and baseline agents without a skill got them right: the
  `org.opencontainers.image.source` label, `packages: write`, "Manage Actions access" for a
  403 from another repo, the multi-arch untagged-cleanup pitfall; `attest-build-provenance` /
  `attest-sbom`, verification pinned to signer workflow, tag ref and digest, Enterprise Cloud
  for private repos, dependency-review, the dependency-graph SBOM export; private
  vulnerability reporting, the advisory lifecycle API, CVE requests, temporary private forks,
  Dependabot alerting only after review. Their one miss, unpinned actions, is covered by
  `github-actions-hardening` and `pins.py`.

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
- From a skills.sh search (`npx skills find`, 2026-11-28) for the medium gaps:
  `wshobson/agents@github-actions-templates` (MIT, 18.7K installs: 19 unpinned actions, almost
  no `permissions:`), `trailofbits/skills@devcontainer-setup` (CC-BY-SA-4.0, the same
  share-alike problem as `netresearch`), `github/awesome-copilot@gh-cli` (overlaps the bundled
  `gh` skill). Nothing reputable found for OIDC, environments, GHCR, attestations,
  advisories, Projects v2 or GraphQL. `github-codespaces-efficiency` was copied.

## Packaging

- [ ] opencode plugin package under `opencode/`, if the HTTP skill catalog isn't enough.
- [ ] Codex manifest under `codex/`, only if Codex stops reading `.claude-plugin/plugin.json`.
