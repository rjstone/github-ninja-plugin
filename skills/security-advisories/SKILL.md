---
name: security-advisories
description: 'Use when setting up private vulnerability reporting or a SECURITY.md, handling a privately reported vulnerability on GitHub (repository security advisory, temporary private fork, CVE request, credits, publishing), or reporting a vulnerability to another repo''s maintainers.'
metadata:
  version: "0.1.1"
---

# Repository security advisories

All calls are `gh api` against `repos/{owner}/{repo}/...`. Writes need admin or security-manager
rights (classic token `repo` or `repository_advisories:write`; fine-grained "Repository security
advisories: write").

## Accepting reports

- Enable private vulnerability reporting: `gh api -X PUT repos/{o}/{r}/private-vulnerability-reporting`
  (check: `gh api repos/{o}/{r}/private-vulnerability-reporting` -> `{"enabled": true}`).
- `SECURITY.md` (root, `.github/` or `docs/`) points reporters to
  `https://github.com/{o}/{r}/security/advisories/new` and asks them not to open public issues.

## Handling a report: edit the draft, never create a second advisory

A private report **already is** a repository advisory, in state `triage`. Work on that one:

1. Find it: `gh api repos/{o}/{r}/security-advisories --jq '.[] | {ghsa_id, state, summary}'`.
2. Accept and fill it in with one PATCH: `state: "draft"` (`closed` rejects it), plus details,
   credits and collaborators in the same call:

```bash
gh api -X PATCH repos/{o}/{r}/security-advisories/GHSA-xxxx-xxxx-xxxx --input - <<'EOF'
{ "state": "draft",
  "summary": "Prototype pollution in merge()",
  "description": "### Impact\n...\n### Patches\nFixed in 2.4.1.\n### Workarounds\n...",
  "vulnerabilities": [{ "package": {"ecosystem": "npm", "name": "@acme/widget"},
      "vulnerable_version_range": "< 2.4.1", "patched_versions": "2.4.1" }],
  "cvss_vector_string": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:H/A:L",
  "cwe_ids": ["CWE-1321"],
  "credits": [{"login": "reporter-login", "type": "reporter"}],
  "collaborating_users": ["reporter-login", "co-maintainer"] }
EOF
```

- `package.name` is the name in the package registry, read from the manifest (`package.json`
  `name`, `pyproject.toml` `[project] name`, ...), never the GitHub `owner/repo`. npm: scoped is
  `@scope/name`, unscoped has no slash. Dependabot matches on it.
- `severity` or `cvss_vector_string`, not both. Credit types: `finder`, `reporter`, `analyst`,
  `coordinator`, `remediation_developer`, `remediation_reviewer`, `remediation_verifier`,
  `tool`, `sponsor`, `other`; credited users must accept before it shows.
- `collaborating_users` / `collaborating_teams` give those people write access to the advisory
  (and to its private fork). Not the repo's collaborator list.

3. Fix in a temporary private fork: `gh api -X POST repos/{o}/{r}/security-advisories/{ghsa}/forks`
   (created asynchronously; Actions don't run there, test locally). Merge its PR from the
   advisory page only when the release is ready to go out right after.
4. CVE: `gh api -X POST repos/{o}/{r}/security-advisories/{ghsa}/cve`. GitHub is the CNA.
   **Public repos only**; for a private repo, use another CNA and set `cve_id`.
5. Disclose in this order, the same day:
   1. CVE requested and assigned (step 4).
   2. Merge the fix to the public default branch (from the advisory page).
   3. Release and publish the fixed package version.
   4. Publish the advisory:
      `gh api -X PATCH repos/{o}/{r}/security-advisories/{ghsa} -f state=published`.
      There is no `/publish` endpoint.

Advisories, private forks and collaborators work on private repos too; only the CVE request
needs a public repo.

## After publishing

- Dependabot alerts users only after GitHub **reviews** the advisory into the Advisory
  Database (`gh api advisories/{ghsa} --jq .type` -> `reviewed`), and only for repos whose
  dependency graph has the same ecosystem, package name and a version in the range.
- A published advisory can still be edited (references, ranges) with the same PATCH.

## A vulnerability in someone else's repo

Report it privately, not as an issue: their `SECURITY.md`, or if they enabled private reporting
(`gh api repos/{o}/{r}/private-vulnerability-reporting`), `POST
repos/{o}/{r}/security-advisories/reports` with `summary`, `description` and `vulnerabilities`
(`package.ecosystem`, `package.name`). If neither exists, ask the user how to reach the
maintainers; don't guess an email address or a third party. Your own package gets its own advisory only if its own
code is affected.
