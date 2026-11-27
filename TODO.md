# TODO

Open work for github-ninja. Done items are removed (the history is in git and `CHANGELOG.md`).

## New skills (our own; nothing suitable exists upstream)

A search of skills.sh (2026-11-27) found no general skill for either topic worth copying.
These would be our own text, so they get a closer review than copied skills, and they carry no
`metadata.upstream` (the upstream sync skips them).

- [ ] **`github-pages`**: publishing a site with GitHub Pages.
  - choose between deploying from a branch and deploying from Actions, and when each fits;
  - the official Actions flow (`actions/configure-pages`, `actions/upload-pages-artifact`,
    `actions/deploy-pages`), pinned by commit SHA, with the `pages: write` and
    `id-token: write` permissions and the `github-pages` environment;
  - enabling and configuring Pages with `gh api` (`repos/{owner}/{repo}/pages`);
  - custom domains: `CNAME`, DNS records, domain verification, enforcing HTTPS;
  - Jekyll vs `.nojekyll`, base paths for project sites, and common 404 causes.
  - Existing narrow skills, for reference only: `github/awesome-copilot@publish-to-pages`
    (converting slides and PDFs to a site), `aviz85/claude-skills-library@gh-pages-deploy`
    (no licence: don't copy).
- [ ] **`github-apps`**: building and using GitHub Apps.
  - when an App beats a personal access token or `GITHUB_TOKEN`;
  - creating an App (settings page or manifest flow), choosing the smallest permissions and
    events, installing it on chosen repos;
  - installation tokens: `actions/create-github-app-token` in workflows (pinned by SHA, with
    `client-id`), and JWT-to-installation-token exchange in code;
  - webhooks: payload verification with `X-Hub-Signature-256`, redelivery;
  - private key handling: Actions secrets, rotation, never in the repo;
  - this project's own use (the marketplace notify App) as a worked example.

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
