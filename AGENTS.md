# AGENTS.md

Instructions for coding agents working in this repository (any harness).

## What this repo is

`github-ninja`: GitHub know-how for coding agents (gh CLI and API, GitHub Actions, Dependabot,
code and secret scanning), packaged once and shipped in several harness formats. Today it holds
only skills; commands, agents or hooks may follow.

## Layout rules

- **The repo root is the plugin.** Skills are harness-neutral, so they live once in
  `skills/<name>/SKILL.md` (no per-harness copies, no symlinks: Windows needs admin rights for
  them). A format that needs files elsewhere points its manifest at `skills/` or has a script
  generate the copy.
- Per-format files:
  - Claude Code: `.claude-plugin/plugin.json` (the plugin) and `.claude-plugin/marketplace.json`
    (a one-plugin local marketplace, source `./`). Skills are found in `skills/` by default.
  - skills.sh (`npx skills add rjstone/github-ninja-plugin`): no manifest; it finds `skills/`.
  - opencode HTTP catalog: `skills/index.json`, **generated** by
    `python3 scripts/build_skills_index.py` (never hand-edit; `--check` reports it stale).
  - Code that only one harness can run (an opencode plugin package, a Codex manifest if Codex
    stops reading the Claude one) goes in a top-level folder named after that harness
    (`opencode/`, `codex/`).
- Keep `README.md`'s skill table and install section in sync with `skills/` and the formats.

## Skills

- Frontmatter: `name` (= folder name), `description`, and a `metadata` block with
  `version: "X.Y.Z"`; copied skills also carry `upstream:` (a GitHub tree URL pinned to a commit).
- **Copied skills** (from github/awesome-copilot, cli/cli, ...): copy the folder unchanged, add
  the upstream `LICENSE` as `LICENSE.txt` inside it, add the `metadata` block, and record the
  repo, commit and folder in `NOTICE`. Only copy from repos whose licence allows it (MIT,
  Apache-2.0, ...). List any local edit to a copied skill in `NOTICE`. Before adding, read the
  whole skill: no hidden instructions, no `curl | sh`, no unexpected hosts.
- **Updating from upstream**: copy the newer upstream folder over ours, keep `LICENSE.txt` and
  the `metadata` block, update `upstream:` and `NOTICE` to the new commit, bump the version.
- **Every change to a skill bumps its `metadata.version`** (CI fails otherwise:
  `scripts/check_skill_versions.py`): major for breaking or rewritten guidance, minor for new
  material, patch for fixes and upstream wording updates. Then regenerate `skills/index.json`.
- Prefer stdlib-only Python for any script a skill ships, so it runs without an install step.

## Privacy and safety

This repository is public. Never commit secrets (API keys, tokens) or paths and names from
private repositories or machines.

## Versioning, commits and releases

- **Conventional commits**: `feat:`, `fix:`, `docs:`, `refactor:`, `perf:`, `test:`,
  `chore:`/`ci:`/`build:`, optional scope (`feat(skills): ...`), `!` or a `BREAKING CHANGE:`
  footer for breaking changes. git-cliff groups the changelog by these (`cliff.toml`).
- The plugin version (`.claude-plugin/plugin.json` `version`) is the bundle's release version;
  each skill also has its own `metadata.version`. Adding or removing a skill is at least a minor
  plugin bump.
- **`CHANGELOG.md` is generated**: never edit it by hand
  (`npx git-cliff@2.14.2 -o CHANGELOG.md`).
- Commit straight to `main` unless a change is large enough to want review on a branch.

Releasing `vX.Y.Z`:

1. Set `version` in `.claude-plugin/plugin.json` to `X.Y.Z`.
2. `npx git-cliff@2.14.2 --tag vX.Y.Z -o CHANGELOG.md`, then commit both as
   `chore(release): vX.Y.Z` and push `main`.
3. Tag that commit `vX.Y.Z` and push the tag. Cloud agent sessions can't push tags: ask the
   maintainer. `.github/workflows/release.yml` then publishes a GitHub Release with git-cliff's
   notes.
4. `.github/workflows/notify-marketplace.yml` starts `rjstone/plugin-marketplace`'s update
   workflow, which points the `github-ninja@rjstone` entry at the new tag (otherwise its daily
   run does). It needs, in this repo's Actions settings, the variable
   `MARKETPLACE_APP_CLIENT_ID` and the secret `MARKETPLACE_APP_PRIVATE_KEY`. For a tag pushed
   before those were set, run the workflow by hand from the Actions tab.

Tags must be `vX.Y.Z` (the marketplace ignores other forms, including `claude plugin tag`'s
`name--vX.Y.Z`).

## CI

`.github/workflows/check.yml` runs on every push and pull request: plugin and marketplace
validation (`claude plugin validate`, both profiles), `skills/index.json` freshness, and the
skill version-bump check. Actions are pinned to commit SHAs (version in a comment) with
`permissions: contents: read`; pass event values to scripts through `env:`, never by `${{ }}`
inside `run:`.
