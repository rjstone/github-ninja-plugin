---
name: repo-badges
description: 'Use when adding, fixing or restyling README badges: CI status, test counts, version, license, coverage or "built with" tech badges, shields.io static badge URLs and logos, badges generated in CI and hosted in the repo without a badge service, or a badge that shows a broken image, the wrong logo or an old value.'
metadata:
  version: "0.1.0"
---

# README badges

A badge is a small SVG image. Pick where it comes from first:

| Need | Use |
|---|---|
| Pass/fail of one workflow, nothing else | GitHub's own badge (below); render it in CI only to match a self-hosted row's style |
| Fixed facts: language, framework, "works with" | a static badge: a shields.io URL, or the same badge rendered once and committed |
| Changing values (test count, version, coverage) with no badge service | render in CI, publish to an orphan `badges` branch (below) |

Never write your own SVG renderer: hand-made badges get text widths wrong. Use a pinned
renderer from the next table.

## Renderers (offline)

| Tool | Install / run | Notes |
|---|---|---|
| `badge-maker` (npm, shields.io's own renderer) | `npx -y -p badge-maker@6.0.0 badge "tests" "42 passed" :brightgreen @flat > tests.svg` | Node ≥ 20, MIT OR Apache-2.0. Styles `flat`, `flat-square`, `plastic`, `for-the-badge`, `social`. No logo slugs: logos only through the API's `logoBase64`. |
| `badgepy` (PyPI) | `uvx --from badgepy==2.0.3 badgepy preset version v1.4.2 -o version.svg`; free form `badgepy --left-text build --right-text passing --right-color '#4c1' -o build.svg` | Python ≥ 3.10, presets `build`, `version`, `license`, `coverage`, `custom`. `--logo` takes a URL or data URI: add `--embed-logo`, or the SVG fetches the logo every time it is viewed. Maintained fork of the archived `pybadges` (which breaks on Python 3.13+). |
| `gradient-badge` (npm) | API only: `require('gradient-badge')({subject, status, gradient: ['pink', 'F78642']})` | Gradient fills. No CLI, last release 2020, badgen field names (`subject`/`status`). Use only when gradients are asked for. |

Pin the exact version, as above, and check it with `npm view <pkg> version` or PyPI before
writing it down.

## Static badges with shields.io

`https://img.shields.io/badge/<label>-<message>-<color>?style=flat&logo=<slug>&logoColor=white`

- Escaping in the path: `-` → `--`, `_` → `__`, space → `_` or `%20`, `%` → `%25`, `/` → `%2F`,
  `+` → `%2B`. Leave out `<label>-` for a one-part badge: `/badge/<message>-<color>`.
- `logo` is a [Simple Icons](https://simpleicons.org) slug: look it up in
  [`slugs.md`](https://github.com/simple-icons/simple-icons/blob/develop/slugs.md) (title →
  slug; usually lowercase with spaces and punctuation removed). Take the brand hex from
  `data/simple-icons.json` (by `title`). shields.io can lag new
  Simple Icons releases: if a logo does not appear, use the fallback below.
- `logoWidth` was removed (shields.io, 2025-04). It is silently ignored: use `logoSize=auto` for
  wide logos, and tell the user you replaced it (same for any parameter you drop). `logoColor` and `logoSize` work only on Simple Icons logos.
- `link=` works only inside `<object>`, not in Markdown or `<img>`: wrap the image in a Markdown
  link instead.
- One style per row. Mixing `for-the-badge` with `flat` makes a ragged row.
- Catalogue to copy from: [inttter/md-badges](https://github.com/inttter/md-badges) (MIT),
  hundreds of ready badges in README tables (search with Ctrl+F; no machine-readable list). Its
  badges link to `(#)`: replace with a real link. Fix slug case to lowercase.

Logo fallback when Simple Icons has none (or shields.io doesn't have it yet):

1. Get an SVG from [svgl](https://svgl.app/docs/api): `https://api.svgl.app?search=<name>`
   returns `[{title, route, ...}]`; `route` is the SVG URL (or `{light, dark}`). Rate-limited:
   fetch once, keep the file. Or take the SVG straight from the repo,
   [pheralb/svgl](https://github.com/pheralb/svgl).
2. Base64 it and pass it as a data URI: shields.io `?logo=data:image/svg%2bxml;base64,<b64>`
   (`+` must be `%2b`), `badgepy --logo <file or data URI> --embed-logo`, or `badge-maker`'s
   `logoBase64` in the API.

Check a logo offline (shields.io unreachable): render the same badge with `badge-maker`'s API,
`logoBase64` set to the icon from the `simple-icons` npm package, and open the SVG. If the
slug isn't in that package, shields.io doesn't have it either.

Brand logos stay their owners' trademarks, whatever the collection's license (Simple Icons is
CC0, the svgl repo is MIT): whether a use is allowed depends on the trademark owner's terms.
Describe use ("works with Claude"), don't imply endorsement.

[New Shields](https://newshields.vercel.app/docs) (`/api/badge.svg?label=&title=&icon=<svgl
slug>&theme=`) is a separate personal project, not a shields fork: icons are svgl slugs, unknown
themes fall back silently, responses are cached for a year (change the URL to refresh), 60
requests per minute.

## Workflow status badge (GitHub)

`https://github.com/<owner>/<repo>/actions/workflows/<file>.yml/badge.svg?branch=main` (also
`&event=push`). Without `branch` it shows the last run on any branch. Not visible to outsiders
for private repos.

## Badges rendered in CI, hosted in the repo

The README links `https://raw.githubusercontent.com/<owner>/<repo>/badges/<name>.svg`. A job
after the tests renders the SVGs and force-pushes them as the only commit of an orphan branch
`badges`, so the branch never grows and `main` gets no commits:

```yaml
permissions:
  contents: read                      # workflow default; only the badges job widens it
jobs:
  test:
    runs-on: ubuntu-latest
    outputs:                          # job level; names match the count step's id
      passed: ${{ steps.count.outputs.passed }}
      failed: ${{ steps.count.outputs.failed }}
    steps:
      # ...checkout and setup as before, then:
      - run: python -m pytest -q --junitxml="$RUNNER_TEMP/junit.xml"
      - name: Count tests
        id: count
        if: always()                  # also after failures; no report (collection error) -> 0
        run: |
          python - "$RUNNER_TEMP/junit.xml" >> "$GITHUB_OUTPUT" <<'PY'
          import sys, xml.etree.ElementTree as ET
          try: r = ET.parse(sys.argv[1]).getroot()
          except (OSError, ET.ParseError): print("passed=0\nfailed=0"); sys.exit()
          s = [r] if r.tag == "testsuite" else r.findall("testsuite")
          n = lambda k: sum(int(x.get(k, 0)) for x in s)
          print(f"passed={n('tests') - n('failures') - n('errors') - n('skipped')}\nfailed={n('failures') + n('errors')}")
          PY

  badges:
    needs: test
    if: always() && github.event_name == 'push' && github.ref == 'refs/heads/main' && github.repository == 'OWNER/REPO'
    runs-on: ubuntu-latest
    permissions:
      contents: write                 # only this job; the workflow default stays read
    concurrency: { group: badges, cancel-in-progress: true }
    steps:
      - uses: actions/checkout@<sha>  # vX.Y.Z; SHAs looked up, see below
        with: { persist-credentials: false }
      - uses: actions/setup-node@<sha> # vX.Y.Z
        with: { node-version: 22 }
      - name: Render
        env:                          # event values through env, never ${{ }} inside run
          RESULT: ${{ needs.test.result }}
          PASSED: ${{ needs.test.outputs.passed }}
          FAILED: ${{ needs.test.outputs.failed }}
        run: |
          read -r VERSION LICENSE < <(python3 -c 'import tomllib; p = tomllib.load(open("pyproject.toml", "rb"))["project"]; l = p.get("license", "unknown"); print(p["version"], l if isinstance(l, str) else l.get("text", "unknown"))')
          case "$RESULT" in success) c=brightgreen; m=passing ;; failure) c=red; m=failing ;; *) c=lightgrey; m=$RESULT ;; esac
          if [ "${FAILED:-0}" != 0 ]; then t="$FAILED failed"; tc=red; else t="${PASSED:-0} passed"; tc=brightgreen; fi
          mkdir -p "$RUNNER_TEMP/b" && cd "$RUNNER_TEMP/b"
          bm() { npx -y -p badge-maker@6.0.0 badge "$@"; }
          bm check "$m" ":$c" > check.svg
          bm tests "$t" ":$tc" > tests.svg
          bm version "v$VERSION" :blue > version.svg
          bm license "$LICENSE" :blue > license.svg
      - name: Publish
        env: { GH_TOKEN: "${{ github.token }}", REPO: "${{ github.repository }}" }
        run: |
          cd "$RUNNER_TEMP/b"
          git init -q -b badges
          git add -A
          git -c user.name='github-actions[bot]' -c user.email='41898282+github-actions[bot]@users.noreply.github.com' \
            commit -q -m "badges for $GITHUB_SHA"
          git push -q --force "https://x-access-token:$GH_TOKEN@github.com/$REPO.git" badges
```

- Counts come from the test runner's own summary, in a step with `if: always()`: pytest
  `--junitxml` (above), unittest's `Ran N tests` and `FAILED (failures=…, errors=…)`, or
  `node --test`'s `# pass N` / `# fail N` lines. For Node, save the log in the test step
  (`shell: bash` makes the pipe keep `npm test`'s exit code) and read it in the count step:

  ```yaml
      - run: npm test 2>&1 | tee "$RUNNER_TEMP/test.log"
        shell: bash
      - id: count
        if: always()
        run: |
          echo "passed=$(sed -n 's/^# pass //p' "$RUNNER_TEMP/test.log" 2>/dev/null | tail -1)" >> "$GITHUB_OUTPUT"
          echo "failed=$(sed -n 's/^# fail //p' "$RUNNER_TEMP/test.log" 2>/dev/null | tail -1)" >> "$GITHUB_OUTPUT"
  ```

  (An empty value counts as 0: the render step uses `${PASSED:-0}`.)
- Version and license come from the manifest, never typed by hand: `pyproject.toml` as above
  (`license` may be a string or `{text = ...}`), `package.json` with
  `node -p "require('./package.json').version"`.
- Look up every action SHA, never write one from memory:
  `git ls-remote --tags https://github.com/actions/setup-node 'v6*'`: a line ending in `^{}` is
  the commit of an annotated tag; without one, the SHA shown is the commit. (`gh api
  repos/<o>/<r>/git/ref/tags/<tag>` works too, but returns the tag object for annotated tags.)
- The workflow never runs this job for `pull_request` or `pull_request_target`: a fork's PR
  would otherwise publish its numbers, or run fork code with a write token.

## When a badge looks wrong

| Symptom | Cause | Fix |
|---|---|---|
| Broken image | `github.com/.../blob/...svg` is an HTML page; or the branch or file doesn't exist yet | `raw.githubusercontent.com/<o>/<r>/<branch>/<file>.svg`; push to `main` once to create the branch |
| Old value for a few minutes | raw.githubusercontent.com (`max-age=300`) and GitHub's image proxy (camo) cache it | wait; `curl -X PURGE <camo-url>` as a last resort |
| Logo missing | slug wrong or not yet in shields.io's Simple Icons | check `slugs.md`; use the svgl data-URI fallback |
| Logo size ignored | `logoWidth` (removed) | `logoSize=auto` |
| Push denied | job lacks `contents: write`, run from a fork, or a ruleset covers `badges` | permissions on that job; exclude `badges` from the ruleset |
