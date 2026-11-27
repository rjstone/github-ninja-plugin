#!/usr/bin/env python3
"""Fail when a changed skill's metadata.version was not raised.

    python3 scripts/check_skill_versions.py <base-ref>

Compares every skills/<name>/ folder that differs between <base-ref> and the
working tree. A new skill passes; a changed or renamed-into skill must have a
higher metadata.version (semver X.Y.Z) than at <base-ref>. A deleted skill
passes. An all-zero or missing base (first push of a branch) checks nothing.
Standard library only.
"""
import os
import re
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTMATTER = re.compile(r"^---\r?\n(.*?)\r?\n---\r?\n", re.S)
VERSION = re.compile(r'^\s+version:\s*"?([0-9]+)\.([0-9]+)\.([0-9]+)"?\s*$', re.M)


def git(*args):
    return subprocess.run(["git", *args], cwd=REPO_ROOT, check=True,
                          capture_output=True, text=True).stdout


def version_of(text):
    m = FRONTMATTER.match(text or "")
    v = VERSION.search(m.group(1)) if m else None
    return tuple(int(x) for x in v.groups()) if v else None


def main(argv):
    if len(argv) != 2:
        print(__doc__)
        return 2
    base = argv[1]
    if not base or set(base) == {"0"}:
        print("no base commit: nothing to compare")
        return 0
    try:
        git("cat-file", "-e", base + "^{commit}")
    except subprocess.CalledProcessError:
        print("base %s not available: nothing to compare" % base)
        return 0
    changed = git("diff", "--name-only", base, "--", "skills/").split()
    names = sorted({p.split("/")[1] for p in changed if p.count("/") >= 2})
    status = 0
    for name in names:
        md = os.path.join(REPO_ROOT, "skills", name, "SKILL.md")
        if not os.path.isfile(md):
            print("ok: %s removed" % name)
            continue
        with open(md, encoding="utf-8") as f:
            new = version_of(f.read())
        if new is None:
            print("::error file=skills/%s/SKILL.md::no metadata.version X.Y.Z" % name)
            status = 1
            continue
        try:
            old = version_of(git("show", "%s:skills/%s/SKILL.md" % (base, name)))
        except subprocess.CalledProcessError:
            old = None
        if old is None:
            print("ok: %s is new (%s)" % (name, ".".join(map(str, new))))
        elif new > old:
            print("ok: %s %s -> %s" % (name, ".".join(map(str, old)), ".".join(map(str, new))))
        else:
            print("::error file=skills/%s/SKILL.md::changed without a version bump (still %s)"
                  % (name, ".".join(map(str, new))))
            status = 1
    if not names:
        print("no skill changes")
    return status


if __name__ == "__main__":
    sys.exit(main(sys.argv))
