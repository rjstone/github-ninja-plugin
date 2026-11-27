# TODO

Open work for github-ninja. Done items are removed (the history is in git and `CHANGELOG.md`).

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

## Packaging

- [ ] opencode plugin package under `opencode/`, if the HTTP skill catalog isn't enough.
- [ ] Codex manifest under `codex/`, only if Codex stops reading `.claude-plugin/plugin.json`.
