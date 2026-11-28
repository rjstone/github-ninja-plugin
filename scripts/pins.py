#!/usr/bin/env python3
"""Version pins for tools that copied skills install (skill-pins.json).

    python3 scripts/pins.py --check     # every pin is applied at its recorded version (CI)
    python3 scripts/pins.py --apply     # (re)write every pin into its skill file
    python3 scripts/pins.py --update [--summary out.md] [--github-output "$GITHUB_OUTPUT"]
                                        # move pins to the newest release, bump skill versions

skill-pins.json maps a skill name to a list of pins:

    {"gh-attach": [{
        "file": "SKILL.md",
        "match": "gh extension install sudosubin/gh-attach(?: --pin \\\\S+)?",
        "replace": "gh extension install sudosubin/gh-attach --pin {version}",
        "repo": "sudosubin/gh-attach",
        "version": "v0.5.1"}]}

`match` is a Python regex that finds the install text in upstream's wording, pinned or not;
`replace` is what we write instead ({version} is filled in). A pin whose `match` no longer
finds anything is an error: upstream reworded the line, and someone has to look.
`--update` takes the highest plain vX.Y.Z (or X.Y.Z) tag of `repo` (no pre-releases) from
`git ls-remote`. sync_upstream.py calls apply_pins() after copying an upstream folder, so the
pins survive upstream updates and don't count as local edits. Standard library plus git.

Action pins need no entry in skill-pins.json. In skills written here (no metadata.upstream:
the upstream sync owns copied skills), every line like

    uses: actions/checkout@<40-hex commit> # v7.0.1

is an action pin. --check looks the tag up with `git ls-remote` and fails unless the SHA is
that tag's commit (an annotated tag is followed to its commit). --update moves each one to the
action repo's newest plain vX.Y.Z tag, rewrites SHA and comment, and bumps the skill's patch
version. A placeholder such as `@<sha>` is not a pin.
"""
import argparse
import json
import os
import re
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PINS_FILE = os.path.join(REPO_ROOT, "skill-pins.json")
SKILLS = os.path.join(REPO_ROOT, "skills")
TAG = re.compile(r"^v?([0-9]+)\.([0-9]+)\.([0-9]+)$")
ACTION = re.compile(
    r"(uses:\s*)([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)((?:/[^@\s]+)?)@([0-9a-f]{40})(\s*#\s*)(v?[0-9]+\.[0-9]+\.[0-9]+)\b")


def load():
    if not os.path.isfile(PINS_FILE):
        return {}
    with open(PINS_FILE, encoding="utf-8") as f:
        return json.load(f)


def save(pins):
    with open(PINS_FILE, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(pins, indent=2) + "\n")


def pin_text(text, pins, rel):
    """Apply the pins for file `rel` to text. Returns (new_text, [pins that matched nothing])."""
    missing = []
    for p in pins:
        if p["file"] != rel:
            continue
        new, n = re.subn(p["match"], p["replace"].replace("{version}", p["version"]), text)
        if n == 0:
            missing.append(p)
        text = new
    return text, missing


def apply_pins(name, skill_dir, all_pins=None):
    """Write the pins of skill `name` into skill_dir. Returns pins that matched nothing."""
    pins = (load() if all_pins is None else all_pins).get(name, [])
    missing = []
    for rel in sorted({p["file"] for p in pins}):
        path = os.path.join(skill_dir, *rel.split("/"))
        if not os.path.isfile(path):
            missing += [p for p in pins if p["file"] == rel]
            continue
        with open(path, encoding="utf-8") as f:
            text = f.read()
        new, miss = pin_text(text, pins, rel)
        missing += miss
        if new != text:
            with open(path, "w", encoding="utf-8", newline="\n") as f:
                f.write(new)
    return missing


def check(pins):
    status = 0
    for name, plist in sorted(pins.items()):
        for p in plist:
            path = os.path.join(SKILLS, name, *p["file"].split("/"))
            want = p["replace"].replace("{version}", p["version"])
            try:
                with open(path, encoding="utf-8") as f:
                    text = f.read()
            except FileNotFoundError:
                print("::error::%s: pinned file %s is missing" % (name, p["file"]))
                status = 1
                continue
            found = [m.group(0) for m in re.finditer(p["match"], text)]
            if not found:
                print("::error file=skills/%s/%s::pin for %s matches nothing (upstream reworded it?)"
                      % (name, p["file"], p["repo"]))
                status = 1
            elif any(f != want for f in found):
                print("::error file=skills/%s/%s::not pinned to %s: run python3 scripts/pins.py --apply"
                      % (name, p["file"], p["version"]))
                status = 1
            else:
                print("ok: %s pins %s %s" % (name, p["repo"], p["version"]))
    return status


def ls_remote_tags(repo):
    return subprocess.run(["git", "ls-remote", "--tags", "https://github.com/%s.git" % repo],
                          capture_output=True, text=True, check=True).stdout


def tag_commits(out):
    """{tag: commit sha} from `git ls-remote --tags` output; annotated tags give the ^{} line."""
    tags = {}
    for line in out.splitlines():
        sha, ref = line.split("\t")
        name = ref[len("refs/tags/"):]
        if name.endswith("^{}"):
            tags[name[:-3]] = sha
        else:
            tags.setdefault(name, sha)
    return tags


def newest(tags):
    best = None
    for tag in tags:
        m = TAG.match(tag)
        if m:
            key = tuple(int(x) for x in m.groups())
            if best is None or key > best[0]:
                best = (key, tag)
    return best[1] if best else None


def written_here_skills():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import sync_upstream as su
    out = []
    for name in sorted(os.listdir(SKILLS)):
        md = os.path.join(SKILLS, name, "SKILL.md")
        if os.path.isfile(md) and not su.read_meta(md)[1]:
            out.append(name)
    return out


def action_pins(skills=None):
    """[(skill, rel path, line number, repo, sha, tag)] for every action pin in written-here skills."""
    pins = []
    for name in written_here_skills() if skills is None else skills:
        root = os.path.join(SKILLS, name)
        for dirpath, _, files in os.walk(root):
            for fn in sorted(files):
                if not fn.endswith(".md"):
                    continue
                path = os.path.join(dirpath, fn)
                rel = os.path.relpath(path, root).replace(os.sep, "/")
                with open(path, encoding="utf-8") as f:
                    for i, line in enumerate(f, 1):
                        for m in ACTION.finditer(line):
                            pins.append((name, rel, i, m.group(2), m.group(4), m.group(6)))
    return pins


def check_actions(pins, lookup=ls_remote_tags):
    status, cache = 0, {}
    for name, rel, line, repo, sha, tag in pins:
        if repo not in cache:
            cache[repo] = tag_commits(lookup(repo))
        want = cache[repo].get(tag)
        where = "file=skills/%s/%s,line=%d" % (name, rel, line)
        if want is None:
            print("::error %s::%s has no tag %s" % (where, repo, tag))
            status = 1
        elif want != sha:
            print("::error %s::%s@%s is not %s (that tag is %s)" % (where, repo, sha[:12], tag, want[:12]))
            status = 1
        else:
            print("ok: %s %s %s" % (name, repo, tag))
    return status


def update_actions(pins, lookup=ls_remote_tags):
    """Move action pins to their newest tag. Returns bump dicts like update()'s."""
    cache, bumps, by_file = {}, [], {}
    for name, rel, _, repo, sha, tag in pins:
        if repo not in cache:
            tags = tag_commits(lookup(repo))
            new = newest(tags)
            cache[repo] = (new, tags.get(new))
        new, new_sha = cache[repo]
        if new and tag_key(new) > tag_key(tag):
            by_file.setdefault((name, rel), {})[(repo, sha, tag)] = (new_sha, new)
    for (name, rel), moves in sorted(by_file.items()):
        path = os.path.join(SKILLS, name, *rel.split("/"))
        with open(path, encoding="utf-8") as f:
            text = f.read()

        def sub(m):
            key = (m.group(2), m.group(4), m.group(6))
            if key not in moves:
                return m.group(0)
            new_sha, new = moves[key]
            return "%s%s%s@%s%s%s" % (m.group(1), m.group(2), m.group(3), new_sha, m.group(5), new)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(ACTION.sub(sub, text))
        for (repo, _, old), (_, new) in sorted(moves.items()):
            if not any((b["skill"], b["repo"], b["old"]) == (name, repo, old) for b in bumps):
                bumps.append(dict(skill=name, repo=repo, old=old, new=new))
    for name in sorted({b["skill"] for b in bumps}):
        frm, to = bump_skill_patch(name)
        for b in bumps:
            if b["skill"] == name:
                b["skill_version"] = "%s -> %s" % (frm, to)
    return bumps


def latest_tag(repo):
    out = ls_remote_tags(repo)
    best = None
    for line in out.splitlines():
        ref = line.split("\t")[1]
        if ref.endswith("^{}"):
            continue
        tag = ref[len("refs/tags/"):]
        m = TAG.match(tag)
        if m:
            key = tuple(int(x) for x in m.groups())
            if best is None or key > best[0]:
                best = (key, tag)
    return best[1] if best else None


def tag_key(tag):
    m = TAG.match(tag or "")
    return tuple(int(x) for x in m.groups()) if m else (-1,)


def bump_skill_patch(name):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import sync_upstream as su
    md = os.path.join(SKILLS, name, "SKILL.md")
    version, upstream = su.read_meta(md)
    new = su.bump(version, minor=False)
    su.set_meta(md, new, upstream)
    return version, new


def update(pins, summary, github_output):
    bumps = []
    for name, plist in sorted(pins.items()):
        changed = False
        for p in plist:
            tag = latest_tag(p["repo"])
            if tag and tag_key(tag) > tag_key(p["version"]):
                print("%s: %s %s -> %s" % (name, p["repo"], p["version"], tag))
                bumps.append(dict(skill=name, repo=p["repo"], old=p["version"], new=tag))
                p["version"] = tag
                changed = True
            else:
                print("%s: %s %s is the latest" % (name, p["repo"], p["version"]))
        if changed:
            missing = apply_pins(name, os.path.join(SKILLS, name), pins)
            if missing:
                raise SystemExit("%s: pin matches nothing; fix skill-pins.json" % name)
            frm, to = bump_skill_patch(name)
            for b in bumps:
                if b["skill"] == name:
                    b["skill_version"] = "%s -> %s" % (frm, to)
    if bumps:
        save(pins)
    bumps += update_actions(action_pins())
    if summary:
        lines = ["Pinned tool and action version bumps, opened and kept current by",
                 "`.github/workflows/upstream-sync.yml` (deps). Skill content updates come in a",
                 "separate PR.", "",
                 "| Skill | Tool | Version | Skill version |", "|---|---|---|---|"]
        for b in bumps:
            lines.append("| `%s` | [%s](https://github.com/%s/compare/%s...%s) | %s -> %s | %s |" % (
                b["skill"], b["repo"], b["repo"], b["old"], b["new"], b["old"], b["new"],
                b.get("skill_version", "")))
        lines += ["", "Before merging: read the tool's release notes and diff, and check the release",
                  "still ships binaries for the platforms the skill supports."]
        with open(summary, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
    if github_output:
        with open(github_output, "a", encoding="utf-8") as f:
            f.write("changed=%s\n" % ("true" if bumps else "false"))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", action="store_true")
    g.add_argument("--apply", action="store_true")
    g.add_argument("--update", action="store_true")
    ap.add_argument("--summary")
    ap.add_argument("--github-output")
    a = ap.parse_args(argv)
    pins = load()
    if a.check:
        return check(pins) | check_actions(action_pins())
    if a.apply:
        status = 0
        for name in sorted(pins):
            for p in apply_pins(name, os.path.join(SKILLS, name), pins):
                print("::error::%s: pin for %s matches nothing" % (name, p["repo"]))
                status = 1
        return status
    return update(pins, a.summary, a.github_output)


if __name__ == "__main__":
    sys.exit(main())
