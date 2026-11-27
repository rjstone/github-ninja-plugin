#!/usr/bin/env python3
"""Check copied skills against their upstream repos and optionally pull in updates.

    python3 scripts/sync_upstream.py                 # report only (exit 0)
    python3 scripts/sync_upstream.py --apply         # rewrite skills/ with upstream updates
    python3 scripts/sync_upstream.py --apply --summary out.md --github-output "$GITHUB_OUTPUT"

A copied skill has `metadata.upstream` in its SKILL.md frontmatter: a GitHub tree URL pinned to
a commit, https://github.com/<owner>/<repo>/tree/<sha>/<path>. For each upstream repo this
fetches the default branch head and the pinned commits (trees only, no file contents) and
compares the skill folder's git tree id at both. Only a folder whose tree changed is fetched
and copied.

Applying an update to skills/<name>/:
- replace the folder with upstream's, keeping our LICENSE.txt name (refreshed from upstream's
  root LICENSE file at the new commit);
- re-add our metadata block: `upstream` pinned to the new commit, `version` bumped from ours
  (minor when files were added or removed, else patch).

Upstream content is only copied, never executed. Standard library plus the git CLI.
"""
import argparse
import filecmp
import os
import re
import shutil
import subprocess
import sys
import tempfile

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS = os.path.join(REPO_ROOT, "skills")
FRONTMATTER = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n", re.S)
UPSTREAM_URL = re.compile(
    r"^https://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)/tree/([0-9a-f]{40})/(.+?)/?$")
VERSION = re.compile(r"^([0-9]+)\.([0-9]+)\.([0-9]+)$")
LICENSE_NAMES = ("LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING")
OURS = ("LICENSE.txt",)  # files we add to a copied folder


def git(*args, cwd=None, check=True):
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    if check and r.returncode:
        raise RuntimeError("git %s failed: %s" % (" ".join(args), r.stderr.strip()))
    return r.stdout.strip()


def split_frontmatter(text):
    m = FRONTMATTER.match(text)
    if not m:
        return None, text
    return m.group(1).split("\n"), text[m.end():]


def read_meta(skill_md):
    """Return (version, upstream) from the frontmatter's metadata block."""
    with open(skill_md, encoding="utf-8") as f:
        fm, _ = split_frontmatter(f.read())
    meta, inside = {}, False
    for line in fm or []:
        if re.match(r"^metadata:\s*$", line):
            inside = True
            continue
        if inside:
            m = re.match(r'^\s+([A-Za-z_-]+):\s*"?(.*?)"?\s*$', line)
            if m and line[:1].isspace():
                meta[m.group(1)] = m.group(2)
            elif line.strip() and not line[:1].isspace():
                inside = False
    return meta.get("version"), meta.get("upstream")


def set_meta(skill_md, version, upstream):
    """Write our metadata keys into SKILL.md, merging with an upstream metadata block."""
    with open(skill_md, encoding="utf-8") as f:
        text = f.read()
    fm, body = split_frontmatter(text)
    if fm is None:
        raise SystemExit("%s: no frontmatter" % skill_md)
    ours = ['  version: "%s"' % version, '  upstream: "%s"' % upstream]
    out, i, merged = [], 0, False
    while i < len(fm):
        line = fm[i]
        out.append(line)
        i += 1
        if re.match(r"^metadata:\s*$", line):
            out.extend(ours)
            while i < len(fm) and (fm[i][:1].isspace() or not fm[i].strip()):
                if not re.match(r"^\s+(version|upstream):", fm[i]):
                    out.append(fm[i])
                i += 1
            merged = True
    if not merged:
        out.append("metadata:")
        out.extend(ours)
    with open(skill_md, "w", encoding="utf-8", newline="\n") as f:
        f.write("---\n" + "\n".join(out) + "\n---\n" + body)


def bump(version, minor):
    m = VERSION.match(version or "")
    if not m:
        return "1.0.0"
    a, b, c = (int(x) for x in m.groups())
    return "%d.%d.0" % (a, b + 1) if minor else "%d.%d.%d" % (a, b, c + 1)


def tree_files(clone, rev, path):
    out = git("ls-tree", "-r", "--name-only", "%s:%s" % (rev, path), cwd=clone, check=False)
    return set(out.split("\n")) if out else set()


def tree_id(clone, rev, path):
    return git("rev-parse", "--verify", "-q", "%s:%s" % (rev, path), cwd=clone, check=False) or None


def folder_matches_upstream(local_dir, clone, rev, path):
    """True when our folder (minus our own files and the metadata block) equals upstream at rev."""
    up = tree_files(clone, rev, path)
    mine = set()
    for dp, dn, fn in os.walk(local_dir):
        dn[:] = [d for d in dn if d != "__pycache__"]
        for n in fn:
            rel = os.path.relpath(os.path.join(dp, n), local_dir).replace(os.sep, "/")
            if rel not in OURS:
                mine.add(rel)
    if up != mine:
        return False
    for rel in up:
        theirs = git("show", "%s:%s/%s" % (rev, path, rel), cwd=clone)
        with open(os.path.join(local_dir, rel), encoding="utf-8", errors="replace") as f:
            local = f.read().strip()
        if rel == "SKILL.md":
            local = strip_our_meta(local)
            theirs = strip_our_meta(theirs)
        if local != theirs.strip():
            return False
    return True


def strip_our_meta(text):
    fm, body = split_frontmatter(text + ("\n" if not text.endswith("\n") else ""))
    if fm is None:
        return text.strip()
    keep, inside = [], False
    for line in fm:
        if re.match(r"^metadata:\s*$", line):
            inside = True
            keep.append(line)
            continue
        if inside and re.match(r"^\s+(version|upstream):", line):
            continue
        if inside and line.strip() and not line[:1].isspace():
            inside = False
        keep.append(line)
    if keep and keep[-1] == "metadata:":
        keep.pop()
    return ("---\n" + "\n".join(keep) + "\n---\n" + body).strip()


def export(clone, rev, path, dest):
    """Write upstream's folder at rev into dest (fetching blobs on demand)."""
    for rel in sorted(tree_files(clone, rev, path)):
        target = os.path.join(dest, *rel.split("/"))
        os.makedirs(os.path.dirname(target), exist_ok=True)
        data = subprocess.run(["git", "show", "%s:%s/%s" % (rev, path, rel)], cwd=clone,
                              capture_output=True, check=True).stdout
        with open(target, "wb") as f:
            f.write(data)


def upstream_license(clone, rev):
    for name in LICENSE_NAMES:
        r = subprocess.run(["git", "show", "%s:%s" % (rev, name)], cwd=clone, capture_output=True)
        if r.returncode == 0:
            return r.stdout
    return None


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--apply", action="store_true", help="rewrite skills/ with upstream updates")
    ap.add_argument("--summary", help="write a Markdown summary (PR body) here")
    ap.add_argument("--github-output", help="append changed=true|false here")
    a = ap.parse_args(argv)

    skills = {}
    for name in sorted(os.listdir(SKILLS)):
        md = os.path.join(SKILLS, name, "SKILL.md")
        if not os.path.isfile(md):
            continue
        version, upstream = read_meta(md)
        if not upstream:
            continue
        m = UPSTREAM_URL.match(upstream)
        if not m:
            print("::warning file=skills/%s/SKILL.md::metadata.upstream is not a pinned GitHub tree URL" % name)
            continue
        owner, repo, sha, path = m.groups()
        skills[name] = dict(version=version, owner=owner, repo=repo, sha=sha, path=path)

    updates, notes = [], []
    with tempfile.TemporaryDirectory() as tmp:
        for key in sorted({(s["owner"], s["repo"]) for s in skills.values()}):
            owner, repo = key
            url = "https://github.com/%s/%s.git" % key
            clone = os.path.join(tmp, "%s__%s" % key)
            git("init", "-q", clone)
            git("remote", "add", "origin", url, cwd=clone)
            git("config", "remote.origin.promisor", "true", cwd=clone)
            git("config", "remote.origin.partialclonefilter", "blob:none", cwd=clone)
            head_ref = git("ls-remote", "--symref", url, "HEAD").split("\n")[0]
            branch = re.sub(r"^ref:\s*refs/heads/(\S+)\s+HEAD$", r"\1", head_ref)
            pinned = sorted({s["sha"] for s in skills.values() if (s["owner"], s["repo"]) == key})
            git("fetch", "-q", "--depth", "1", "--filter=blob:none", "origin", branch, *pinned, cwd=clone)
            # FETCH_HEAD's first line is the first ref fetched: the default branch head.
            head = git("rev-parse", "FETCH_HEAD", cwd=clone)
            date = git("log", "-1", "--format=%cs", head, cwd=clone)
            for name, s in skills.items():
                if (s["owner"], s["repo"]) != key:
                    continue
                old, new = tree_id(clone, s["sha"], s["path"]), tree_id(clone, head, s["path"])
                label = "%s/%s" % key
                if new is None:
                    notes.append("- `%s`: `%s` no longer exists upstream in %s@%s; left as is."
                                 % (name, s["path"], label, head[:7]))
                    print("%s: removed upstream (left as is)" % name)
                    continue
                if old == new:
                    print("%s: up to date (%s@%s)" % (name, label, s["sha"][:7]))
                    continue
                before, after = tree_files(clone, s["sha"], s["path"]), tree_files(clone, head, s["path"])
                minor = before != after
                version = bump(s["version"], minor)
                local_dir = os.path.join(SKILLS, name)
                drift = old is not None and not folder_matches_upstream(local_dir, clone, s["sha"], s["path"])
                print("%s: update %s -> %s (%s -> %s)%s" % (
                    name, s["sha"][:7], head[:7], s["version"], version, ", LOCAL EDITS" if drift else ""))
                updates.append(dict(name=name, label=label, old=s["sha"], new=head, date=date,
                                    path=s["path"], frm=s["version"], to=version, drift=drift,
                                    added=sorted(after - before), removed=sorted(before - after)))
                if not a.apply:
                    continue
                lic_old = os.path.join(local_dir, "LICENSE.txt")
                lic_old = open(lic_old, "rb").read() if os.path.isfile(lic_old) else None
                shutil.rmtree(local_dir)
                export(clone, head, s["path"], local_dir)
                lic = upstream_license(clone, head)
                if lic is not None:
                    with open(os.path.join(local_dir, "LICENSE.txt"), "wb") as f:
                        f.write(lic)
                    if lic_old is not None and lic != lic_old:
                        updates[-1]["license_changed"] = True
                upstream = "https://github.com/%s/tree/%s/%s" % (label, head, s["path"])
                set_meta(os.path.join(local_dir, "SKILL.md"), version, upstream)

    if a.summary:
        with open(a.summary, "w", encoding="utf-8") as f:
            f.write(render_summary(updates, notes))
    if a.github_output:
        with open(a.github_output, "a", encoding="utf-8") as f:
            f.write("changed=%s\n" % ("true" if updates else "false"))
    return 0


def render_summary(updates, notes):
    lines = ["Upstream skill updates, opened and kept current by `.github/workflows/upstream-sync.yml`.",
             "Each run rebuilds this branch from `main` with every pending update, so it always",
             "holds all of them. Review the upstream diffs, then merge.", ""]
    if updates:
        lines += ["| Skill | Upstream | Change | Version |", "|---|---|---|---|"]
        for u in updates:
            cmp_url = "https://github.com/%s/compare/%s...%s" % (u["label"], u["old"][:12], u["new"][:12])
            lines.append("| `%s` | %s | [`%s...%s`](%s) (%s) | %s -> %s |" % (
                u["name"], u["label"], u["old"][:7], u["new"][:7], cmp_url, u["date"], u["frm"], u["to"]))
        lines.append("")
        for u in updates:
            extra = []
            if u["added"]:
                extra.append("added: " + ", ".join("`%s`" % x for x in u["added"]))
            if u["removed"]:
                extra.append("removed: " + ", ".join("`%s`" % x for x in u["removed"]))
            if u.get("license_changed"):
                extra.append("**upstream LICENSE text changed: check it still allows copying**")
            if u["drift"]:
                extra.append("**our copy differed from upstream at the old commit (local edits?): "
                             "they were overwritten; re-apply them if still wanted and list them in NOTICE**")
            if extra:
                lines.append("- `%s`: %s" % (u["name"], "; ".join(extra)))
    if notes:
        lines += ["", "Notes:"] + notes
    lines += ["", "Before merging: read each upstream diff (hidden instructions, `curl | sh`, new hosts),",
              "as AGENTS.md asks for any copied skill."]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    sys.exit(main())
