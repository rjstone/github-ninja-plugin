---
name: github-pages
description: 'Publish and troubleshoot a GitHub Pages site. Use when asked to host a static site, docs or demo on GitHub Pages, choose between deploying from a branch and deploying with GitHub Actions, write or fix a Pages deploy workflow, enable or configure Pages through the API, set up a custom domain, DNS and HTTPS, or debug a Pages 404, missing CSS, or a build that does not show up.'
metadata:
  version: "0.1.0"
---

# GitHub Pages

GitHub Pages serves a static site from a repository at `https://<owner>.github.io/` (a user or
organization site, from a repo named `<owner>.github.io`) or `https://<owner>.github.io/<repo>/`
(a project site). Pages only serves files: there is no server-side code.

## 1. Choose the publishing source

| Source | Use when | How it builds |
|---|---|---|
| **GitHub Actions** (recommended) | Any static site generator, any build step, or plain files | Your workflow builds and uploads an artifact; `actions/deploy-pages` publishes it |
| **Deploy from a branch** | Plain HTML, or a Jekyll site GitHub can build itself | GitHub runs its own Jekyll build on a branch and folder (`/` or `/docs`) |

Prefer Actions: you control the build, nothing generated is committed, and the deploy is one job
you can read in the Actions log. Use a branch only for the simplest sites.

Check what a repo uses now:

```sh
gh api repos/{owner}/{repo}/pages --jq '{build_type, source, html_url, cname, https_enforced}'
```

A 404 from that call means Pages isn't enabled.

## 2. Enable Pages

```sh
# Actions as the source
gh api -X POST repos/{owner}/{repo}/pages -f build_type=workflow

# Or a branch and folder
gh api -X POST repos/{owner}/{repo}/pages \
  -f 'source[branch]=main' -f 'source[path]=/docs'

# Switch an existing site to Actions
gh api -X PUT repos/{owner}/{repo}/pages -f build_type=workflow
```

These need admin rights on the repository. Pages on a private repository needs a paid plan.

## 3. The deploy workflow (Actions source)

Pin each action to a full commit SHA (see the `github-actions-hardening` skill) and look up the
newest release before using these; the SHAs below were current on 2026-11-27.

```yaml
name: pages
on:
  push:
    branches: [main]
  workflow_dispatch:
permissions:
  contents: read
concurrency:
  group: pages
  cancel-in-progress: false   # let a running deploy finish
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          persist-credentials: false
      - id: pages
        uses: actions/configure-pages@45bfe0192ca1faeb007ade9deae92b16b8254a0d # v6.0.0
      # Build here. Pass the base path to your generator, e.g.
      #   npm ci && npm run build -- --base "${{ steps.pages.outputs.base_path }}/"
      - uses: actions/upload-pages-artifact@fc324d3547104276b827a68afc52ff2a11cc49c9 # v5.0.0
        with:
          path: ./dist        # the folder holding index.html; the default is _site/
  deploy:
    needs: build
    runs-on: ubuntu-latest
    permissions:
      pages: write            # publish to Pages
      id-token: write         # prove the deploy came from this workflow (OIDC)
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - id: deployment
        uses: actions/deploy-pages@368f82528645a54fb793d4d04e342629a3f51346 # v5.0.1
```

Notes:
- Keep `pages: write` and `id-token: write` on the deploy job only; the build job needs neither.
- The `github-pages` environment is created automatically. Its deployment branch rules decide
  which branches may deploy: if a deploy from another branch is rejected, that is why.
- The artifact must be a folder whose top level holds `index.html`.

## 4. Custom domains

Verify the domain first (account or organization **Settings > Pages > Add a domain**): it stops
anyone else from claiming it for their Pages site (domain takeover).

| Domain | DNS records |
|---|---|
| `www.example.com` or another subdomain | `CNAME` to `<owner>.github.io` (no repo name) |
| `example.com` (apex) | `A`: `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`; optional `AAAA`: `2606:50c0:8000::153`, `2606:50c0:8001::153`, `2606:50c0:8002::153`, `2606:50c0:8003::153`; or an `ALIAS`/`ANAME` to `<owner>.github.io` |

Set up both the apex and `www`: Pages then redirects between them.

Then set the domain on the repo:

```sh
gh api -X PUT repos/{owner}/{repo}/pages -f cname=www.example.com
# once the certificate is issued (can take a while after DNS resolves):
gh api -X PUT repos/{owner}/{repo}/pages -F https_enforced=true
```

- **Actions source:** the domain lives in the repo settings only. A `CNAME` file in the
  artifact is ignored and not needed.
- **Branch source:** saving the domain commits a `CNAME` file to the branch root. Don't delete it.
- Never use wildcard DNS records (`*.example.com`) for Pages: they allow takeover of other
  subdomains.

Check DNS with `dig +short www.example.com CNAME` and `dig +short example.com A`.

## 5. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| 404 on the whole site | Pages not enabled, wrong source folder, or no `index.html` at the artifact or folder root | Check step 2's `gh api` output and the artifact `path` |
| Page loads without CSS or JS, or links 404 | Project site served under `/<repo>/` but assets use `/` | Set the generator's base path (from `configure-pages`' `base_path` output) |
| Files or folders starting with `_` are missing (branch source) | GitHub's Jekyll build drops them | Add an empty `.nojekyll` file at the source root, or use the Actions source |
| A push didn't update the site | The deploy failed, or the browser or CDN cache | Read the latest `pages` workflow run (or "pages build and deployment" for the branch source); hard-reload |
| Deploy job: "Branch is not allowed to deploy" | `github-pages` environment branch rules | Allow the branch in **Settings > Environments > github-pages** |
| Custom domain shows "improperly configured" | DNS not pointing at Pages yet, or a conflicting record | Fix the records in step 4; remove other `A`/`AAAA`/`CNAME` records for that name |
| "Enforce HTTPS" is unavailable | Certificate not issued yet | Wait for DNS to settle; remove and re-add the custom domain to retry |
| Case-sensitive 404 (`About.html` vs `about.html`) | Pages paths are case-sensitive | Match link case to file names |

Limits to keep in mind: sites up to 1 GB, soft limits on bandwidth and on branch builds per hour.
Pages is for static content; don't use it to host secrets or as a file-sharing service.

## Related skills

- `github-actions-hardening`: pinning, permissions and triggers for the deploy workflow.
- `diagnose-ci-gate`: when the Pages deploy job fails.
- `gh`: `gh api` usage and pagination.
