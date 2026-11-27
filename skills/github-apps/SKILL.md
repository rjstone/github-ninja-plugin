---
name: github-apps
description: 'Use when a workflow or service needs a token that outlives or outranks GITHUB_TOKEN (cross-repo access, pushes that must trigger other workflows, dispatching workflows in another repo), when choosing between a GitHub App, a personal access token and GITHUB_TOKEN, when minting installation tokens in Actions or code, when verifying GitHub webhooks, or when rotating or storing an App private key.'
metadata:
  version: "0.2.0"
---

# GitHub Apps

A GitHub App is an identity of its own (`<app-slug>[bot]`) with permissions chosen per App,
installed on chosen repositories. It authenticates with short-lived tokens minted from a private
key, so nothing long-lived belongs to a person.

## 1. Which credential?

| Need | Use |
|---|---|
| A workflow acting on its own repository | `GITHUB_TOKEN`, with a `permissions:` block |
| Acting on another repository, or across an organization | **GitHub App** installation token |
| A push or PR that must start other workflows (`GITHUB_TOKEN` events don't, except `workflow_dispatch` and `repository_dispatch`) | **GitHub App** installation token |
| Starting a workflow in another repository | **GitHub App** with only "Actions: Read and write" on that repository |
| A service, bot or integration that runs outside Actions | **GitHub App** |
| Acting as a person (their own repos, a one-off script) | Fine-grained personal access token, smallest scope, short expiry |

Prefer an App over a personal access token for anything automated: it isn't tied to a person's
account, its permissions are explicit, and its tokens expire after an hour.

## 2. Create the App

1. **Settings > Developer settings > GitHub Apps > New GitHub App** (for an organization:
   the organization's settings).
2. Name, homepage URL (the repo is fine).
3. **Webhook:** untick "Active" unless the App must receive events. A token-only App needs none.
4. **Permissions:** the fewest that work. Start from nothing and add, e.g. "Contents: Read and
   write" to push, "Pull requests: Read and write" to open PRs, "Actions: Read and write" to
   dispatch workflows. Metadata (read) is always granted.
5. **Where can it be installed:** "Only on this account" unless others must install it.
6. Create, then note the **Client ID** (`Iv...`) on the settings page and **generate a private
   key** (a `.pem` download).
7. **Install App** (left menu) on only the repositories it needs.

The manifest flow (`POST` a JSON manifest to `https://github.com/settings/apps/new`, then
`POST /app-manifests/{code}/conversions`) creates an App from code; it suits tools that set up
Apps for others, not one-off setups.

## 3. Tokens in GitHub Actions

Store the Client ID as a variable and the key as a secret (e.g. `APP_CLIENT_ID`,
`APP_PRIVATE_KEY`), then mint a token per job. Pin the action by SHA and check for a newer
release first; this SHA was current on 2026-11-27.

```yaml
permissions:
  contents: read
jobs:
  example:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/create-github-app-token@f418cff399f7aef4c2f0ad47e25ca7a6abbdd6fc # v3.4.0
        id: app
        with:
          client-id: ${{ vars.APP_CLIENT_ID }}
          private-key: ${{ secrets.APP_PRIVATE_KEY }}
          owner: my-org                 # another owner's installation, if needed
          repositories: other-repo      # narrow the token to these repos
      - name: Use it
        env:
          GH_TOKEN: ${{ steps.app.outputs.token }}
        run: gh api repos/my-org/other-repo
```

- Use `client-id` (v3 deprecates the numeric `app-id`).
- Narrow with `repositories:` and, where supported, `permission-<name>:` inputs; the token never
  gets more than the App's installation has.
- The action revokes the token when the job ends.
- Pass the token to scripts through `env:`, never by `${{ }}` inside `run:`.

To push to another repository (the App needs "Contents: Read and write" there), check it out
with the token; a plain `git push` then uses it, and the push starts that repo's workflows:

```yaml
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          repository: my-org/other-repo
          token: ${{ steps.app.outputs.token }}
      # change files, git commit, then: git push
```

If the target branch is protected, add the App to its ruleset's bypass list, or push a branch
and open a pull request instead.

## 4. Tokens in code or scripts

1. **Make a JWT** (RS256, signed with the private key): `iat` 60 seconds in the past (clock
   drift), `exp` at most 10 minutes ahead, `iss` the Client ID (recommended) or App ID.
2. **Find the installation:** `GET /repos/{owner}/{repo}/installation` (or
   `/orgs/{org}/installation`, `/users/{user}/installation`) with `Authorization: Bearer <JWT>`.
   Webhook payloads carry `installation.id` already.
3. **Exchange:** `POST /app/installations/{id}/access_tokens`, optionally with
   `{"repositories": [...], "permissions": {...}}` to narrow it. The token expires after 1 hour;
   mint a new one rather than caching it longer.

Shell version, no libraries beyond `openssl`:

```sh
b64url() { openssl base64 -A | tr '+/' '-_' | tr -d '='; }
now=$(date +%s)
header=$(printf '{"alg":"RS256","typ":"JWT"}' | b64url)
payload=$(printf '{"iat":%d,"exp":%d,"iss":"%s"}' $((now-60)) $((now+540)) "$APP_CLIENT_ID" | b64url)
sig=$(printf '%s.%s' "$header" "$payload" | openssl dgst -sha256 -sign "$KEY_FILE" | b64url)
jwt="$header.$payload.$sig"

inst=$(curl -s -H "Authorization: Bearer $jwt" -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/$OWNER/$REPO/installation" | jq -r .id)
token=$(curl -s -X POST -H "Authorization: Bearer $jwt" -H "Accept: application/vnd.github+json" \
  "https://api.github.com/app/installations/$inst/access_tokens" | jq -r .token)
GH_TOKEN=$token gh api "repos/$OWNER/$REPO"
```

In application code, use the platform's maintained library (Octokit's App auth in JS,
`PyGithub`/`githubkit` in Python) instead of hand-rolling JWTs.

A JWT must be sent as `Authorization: Bearer`. Installation tokens start with `ghs_`, but their
length is not fixed and GitHub has changed token formats before: never validate or store them by
length.

## 5. Webhooks

- Set a **webhook secret** and verify every delivery: compute HMAC-SHA256 of the **raw request
  body** with the secret, hex-encode, prefix `sha256=`, and compare with the
  `X-Hub-Signature-256` header using a constant-time comparison (`hmac.compare_digest` in
  Python, `crypto.timingSafeEqual` in Node). Reject on mismatch or a missing header.
- Verify before parsing JSON, and on the exact bytes received (re-serialized JSON won't match).
- `X-GitHub-Delivery` is a unique delivery ID: use it to drop duplicates, since deliveries can
  repeat.
- Respond within 10 seconds (do the work asynchronously). Failed deliveries can be listed and
  redelivered: `GET /app/hook/deliveries`, `POST /app/hook/deliveries/{id}/attempts` (JWT auth).

```python
import hashlib, hmac
def valid(secret: bytes, body: bytes, header: str | None) -> bool:
    if not header:
        return False
    expected = "sha256=" + hmac.new(secret, body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, header)
```

## 6. Private key handling

- Keep the `.pem` only in a secret store (Actions secret, cloud secret manager). Never commit it,
  print it, or paste it into chat or an issue.
- Rotate: generate a new key on the App's settings page, update the secret, confirm a run works,
  then delete the old key. An App can hold several keys at once, so rotation needs no downtime.
- A leaked key: revoking it beats uptime. Generate a new key and delete the leaked one right
  away, then update the secret; runs fail in between. Tokens already minted from it stay valid
  for up to an hour. Then remove the key where it leaked (an issue or comment keeps old text in
  its edit history: delete it, or ask GitHub Support to purge it) and review what happened
  meanwhile in the installed repositories (commits, releases, workflow runs, settings).
- Review installations and permissions now and then; remove the App from repos it no longer
  needs. Changing an App's permissions asks each installation owner to approve the change.

## Common mistakes

| Symptom | Likely cause | Fix |
|---|---|---|
| `401` "JWT could not be decoded" or "'Expiration time' claim is too far in the future" | `exp` more than 10 minutes ahead, or the local clock is ahead of GitHub's | Keep `exp` under 10 minutes; backdate `iat` by 60 seconds |
| `401` or `404` on `/app/...` or `/repos/{owner}/{repo}/installation` | An installation token sent where a JWT is needed | `/app/...` and the installation lookup take the JWT; everything else takes the installation token |
| `404` on `/repos/{owner}/{repo}/installation` with a valid JWT | The App isn't installed on that repository | Install it there (App settings > Install App) |
| `403` "Resource not accessible by integration" | The App lacks that permission, or the token was narrowed below it | Add the permission to the App, then have the installation owner accept the change |
| The push worked but no workflow ran | The push used `GITHUB_TOKEN` | Push with the App's installation token |
| Every webhook signature check fails | The body was parsed or re-serialized before the check, or the wrong secret is used | Check the raw bytes first, with the App's webhook secret |

## Related skills

- `github-actions-hardening`: token permissions, pinning and `env:` handling in workflows.
- `gh`: `gh api` with `GH_TOKEN` set to an installation token.
