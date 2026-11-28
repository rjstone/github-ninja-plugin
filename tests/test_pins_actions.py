"""Offline tests for action pins in scripts/pins.py (fake `git ls-remote`, temporary skills)."""
import contextlib
import io
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
import pins  # noqa: E402

A = "a" * 40
B = "b" * 40
C = "c" * 40
TAGOBJ = "d" * 40

# actions/x: v1.0.0 lightweight (A), v1.1.0 annotated (tag object TAGOBJ -> commit B), v2.0.0 (C)
LS = {
    "actions/x": "%s\trefs/tags/v1.0.0\n%s\trefs/tags/v1.1.0\n%s\trefs/tags/v1.1.0^{}\n"
                 "%s\trefs/tags/v2.0.0\n%s\trefs/tags/v2-beta\n" % (A, TAGOBJ, B, C, A),
}


def skill(root, name, body, upstream=None):
    os.makedirs(os.path.join(root, name))
    meta = '  version: "0.1.0"\n' + ('  upstream: "%s"\n' % upstream if upstream else "")
    with open(os.path.join(root, name, "SKILL.md"), "w", encoding="utf-8") as f:
        f.write("---\nname: %s\ndescription: x\nmetadata:\n%s---\n\n%s" % (name, meta, body))


class ActionPins(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.old = pins.SKILLS
        pins.SKILLS = self.tmp

    def tearDown(self):
        pins.SKILLS = self.old

    def run_quiet(self, fn, *a, **k):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            r = fn(*a, **k)
        return r, out.getvalue()

    def test_tag_commits_follows_annotated_tags(self):
        t = pins.tag_commits(LS["actions/x"])
        self.assertEqual(t["v1.0.0"], A)
        self.assertEqual(t["v1.1.0"], B)
        self.assertEqual(pins.newest(t), "v2.0.0")

    def test_finds_pins_in_written_here_skills_only(self):
        skill(self.tmp, "ours", "      - uses: actions/x@%s # v1.0.0\n      - uses: actions/x@<sha> # v1.0.0\n" % A)
        skill(self.tmp, "copied", "      - uses: actions/x@%s # v1.0.0\n" % A,
              upstream="https://github.com/o/r/tree/%s/skills/copied" % A)
        found = pins.action_pins()
        self.assertEqual([(p[0], p[3], p[5]) for p in found], [("ours", "actions/x", "v1.0.0")])

    def test_check_passes_for_right_sha_including_annotated(self):
        skill(self.tmp, "ours", "uses: actions/x@%s # v1.0.0\nuses: actions/x/sub@%s # v1.1.0\n" % (A, B))
        status, out = self.run_quiet(pins.check_actions, pins.action_pins(), lambda r: LS[r])
        self.assertEqual(status, 0, out)

    def test_check_fails_for_wrong_sha_or_missing_tag(self):
        skill(self.tmp, "ours", "uses: actions/x@%s # v1.1.0\nuses: actions/x@%s # v9.9.9\n" % (TAGOBJ, A))
        status, out = self.run_quiet(pins.check_actions, pins.action_pins(), lambda r: LS[r])
        self.assertEqual(status, 1)
        self.assertIn("is not v1.1.0", out)
        self.assertIn("has no tag v9.9.9", out)

    def test_update_moves_to_newest_and_bumps_skill(self):
        skill(self.tmp, "ours", "      - uses: actions/x@%s # v1.0.0\n      - uses: actions/x/sub@%s   # v1.1.0\n" % (A, B))
        bumps = pins.update_actions(pins.action_pins(), lambda r: LS[r])
        with open(os.path.join(self.tmp, "ours", "SKILL.md"), encoding="utf-8") as f:
            text = f.read()
        self.assertIn("uses: actions/x@%s # v2.0.0" % C, text)
        self.assertIn("uses: actions/x/sub@%s   # v2.0.0" % C, text)
        self.assertIn('version: "0.1.1"', text)
        self.assertEqual({(b["old"], b["new"]) for b in bumps}, {("v1.0.0", "v2.0.0"), ("v1.1.0", "v2.0.0")})

    def test_update_leaves_latest_alone(self):
        skill(self.tmp, "ours", "uses: actions/x@%s # v2.0.0\n" % C)
        self.assertEqual(pins.update_actions(pins.action_pins(), lambda r: LS[r]), [])
        with open(os.path.join(self.tmp, "ours", "SKILL.md"), encoding="utf-8") as f:
            self.assertIn('version: "0.1.0"', f.read())


if __name__ == "__main__":
    unittest.main()
