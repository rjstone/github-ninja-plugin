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
- The plugin icon is `assets/icon.png` (square PNG, 512-2048 px, under 2 MB; no SVG or WebP),
  named by `"icon"` in `.claude-plugin/plugin.json`. The repo root is the plugin, so one copy
  is enough.
- Keep `README.md`'s skill table and install section in sync with `skills/` and the formats.

## Skills

- Frontmatter: `name` (= folder name), `description`, and a `metadata` block with
  `version: "X.Y.Z"`; copied skills also carry `upstream:` (a GitHub tree URL pinned to a commit).
- **Copied skills** (from github/awesome-copilot, cli/cli, ...): copy the folder unchanged, add
  the upstream `LICENSE` as `LICENSE.txt` inside it, add the `metadata` block, and record the
  repo, commit and folder in `NOTICE`. Only copy from repos whose licence allows it (MIT,
  Apache-2.0, ...). List any local edit to a copied skill in `NOTICE`. Before adding, read the
  whole skill: no hidden instructions, no `curl | sh`, no unexpected hosts.
- **Skills written here** (`github-pages`, `github-apps`, `repo-badges`,
  `github-mcp-config`, `security-advisories`): only for a topic with no upstream
  skill worth copying. They are MIT under the repo's `LICENSE`, so they have no `LICENSE.txt`,
  `metadata.upstream` or `NOTICE` entry, and the upstream sync skips them. Before merging a
  new one or a large change, test it the superpowers `writing-skills` way: give the same tasks
  to a subagent with and without the skill, keep only what fixes a failure seen without it, and
  re-test after the fixes. Pin every action a skill shows as
  `uses: owner/repo@<commit SHA> # vX.Y.Z`, looked up, never from memory: `pins.py --check` (CI)
  fails unless the SHA is that tag's commit, and `--update` (the `deps-sync` PR) moves these pins
  to each action's newest release and bumps the skill's patch version.
- **Updating from upstream** is automated: `.github/workflows/upstream-sync.yml` (daily, or by
  hand) runs `scripts/sync_upstream.py --apply`, which compares each skill's upstream folder at
  its pinned commit with upstream's default branch and, for each changed one, copies the new
  folder, refreshes `LICENSE.txt`, re-pins `metadata.upstream` and bumps `metadata.version`
  (minor if files were added or removed, else patch). All pending updates go on one bot branch,
  `upstream-sync`, rebuilt from `main` on every run, with one PR: a later update to any skill
  joins the open PR. Don't push to `upstream-sync` unless you mean to take it over: the workflow
  stops updating a branch that has non-bot commits. Before merging, read the upstream diffs
  linked in the PR. A skill flagged "local edits" had drifted from upstream and the sync
  overwrote that drift: re-apply what is still wanted and list it in `NOTICE`.
  Report only, locally: `python3 scripts/sync_upstream.py`.
- **Tool pins**: when a copied skill installs a tool (a `gh` extension, an npm package, ...),
  pin it to a release in `skill-pins.json` instead of editing the skill by hand: a regex `match`
  for upstream's install text, the `replace` text with `{version}`, the tool's `repo`, and the
  pinned `version` tag. `python3 scripts/pins.py --apply` writes pins, `--check` (CI) verifies
  them, `--update` moves them to the newest stable release (and does the same for action pins in
  skills written here, which need no entry in `skill-pins.json`). Tests: `tests/` (`unittest`,
  offline). `sync_upstream.py` re-applies pins
  after every upstream update, and a pin is not counted as a local edit. Pin binary (precompiled)
  `gh` extensions to a release tag, the only form `gh extension install --pin` takes for them.
  Tool bumps arrive in their own PR (`deps-sync` branch, `chore(deps): ...`), separate from
  skill content updates (`upstream-sync` branch, `chore(skills): ...`); don't push to either
  branch unless you mean to take it over.
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
skill version-bump check. `upstream-sync.yml` runs the same checks before it pushes its branch
(PRs pushed with `GITHUB_TOKEN` don't start `check.yml`; an optional GitHub App token does:
variable `SYNC_APP_CLIENT_ID`, secret `SYNC_APP_PRIVATE_KEY`). With `GITHUB_TOKEN`, the repo
setting "Allow GitHub Actions to create and approve pull requests" must be on.

README badges are SVG files on the orphan branch `badges`
(`https://raw.githubusercontent.com/rjstone/github-ninja-plugin/badges/<name>.svg`); no badge
service is used (the user, 2026-11-28). On pushes to `main`, `check.yml`'s `badges` job (after
`check`, even when it fails, never on pull requests, the only job with `contents: write`)
renders `check`, `version`, `license` and `skills` (the count of `skills/*/SKILL.md`) with
`bash scripts/badges.sh SPEC OUTDIR` (pinned npm `badge-maker`, offline) and force-pushes them
as the branch's only commit.

Actions are pinned to commit SHAs (version in a comment) with
`permissions: contents: read`; pass event values to scripts through `env:`, never by `${{ }}`
inside `run:`.
