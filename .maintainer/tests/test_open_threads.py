#!/usr/bin/env python3
"""Tests for md/open-threads.py. From the repo root:

    python3 -m unittest discover -s .maintainer/tests
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOL = os.path.join(REPO, "md", "open-threads.py")


def user(body, ts, turn=None):
    m = {"author": "user", "body": body, "ts": ts}
    if turn is not None:
        m["turn"] = turn
    return m


def thread(tid, snippet, messages, heading="Intro", context="", src=None):
    anchor = {"snippet": snippet, "context": context, "heading": heading}
    if src:
        anchor["src"] = src
    return {"id": tid, "title": "", "anchor": anchor, "anchor_status": "ok",
            "messages": messages}


class Pair:
    """A NAME-comments.json / NAME-agent.jsonl / NAME.md trio in a temp dir."""

    def __init__(self, tmp, name="doc"):
        self.store = os.path.join(tmp, name + "-comments.json")
        self.journal = os.path.join(tmp, name + "-agent.jsonl")
        self.doc = os.path.join(tmp, name + ".md")

    def write_store(self, threads, turn=3):
        with open(self.store, "w", encoding="utf-8") as f:
            json.dump({"version": 1, "turn": turn, "threads": threads}, f)

    def write_journal(self, lines):
        with open(self.journal, "w", encoding="utf-8") as f:
            for line in lines:
                f.write(line if isinstance(line, str) else json.dumps(line))
                f.write("\n")

    def write_doc(self, text):
        with open(self.doc, "w", encoding="utf-8") as f:
            f.write(text)

    def run(self, *args):
        return subprocess.run([sys.executable, TOOL, self.store] + list(args),
                              capture_output=True, text=True)


class OpenThreadsTest(unittest.TestCase):

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.pair = Pair(tmp.name)

    # 1
    def test_user_only_thread_needs_you(self):
        edit = "[Edit]\nThe <del>old</del><ins>new</ins> text\n[/Edit]"
        self.pair.write_store([
            thread("t1", "The old text", [user(edit, 100, 1), user("prefer new", 100, 1)]),
        ], turn=1)
        r = self.pair.run()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stderr, "")
        self.assertEqual(r.stdout,
            "store: %s  turn 1  1 threads, 1 need you\n"
            "=== t1  heading: Intro\n"
            "anchor: The old text\n"
            "[user turn 1] %s\n"
            "[user turn 1] prefer new\n" % (self.pair.store, edit))

    def test_context_printed_only_for_short_snippets(self):
        long = "x" * 60
        self.pair.write_store([
            thread("t1", "phone", [user("a", 1, 1)], context="the phone view"),
            thread("t2", long, [user("b", 2, 1)], context="ctx"),
        ])
        out = self.pair.run().stdout
        self.assertIn("anchor: phone\ncontext: the phone view\n", out)
        self.assertIn("anchor: %s\n[user turn 1] b" % long, out)
        self.assertNotIn("context: ctx", out)

    # 2
    def test_resolved_with_body_not_listed(self):
        self.pair.write_store([thread("t1", "s", [user("do it", 100, 1)])])
        self.pair.write_journal([
            {"thread": "t1", "body": "Done.", "status": "resolved", "ts": 200, "turn": 1},
        ])
        r = self.pair.run()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout, "store: %s  turn 3  1 threads, 0 need you\n" % self.pair.store)
        self.assertIn("t1  resolved  last=agent  Intro | s\n", self.pair.run("--all").stdout)

    # 3
    def test_user_follow_up_reopens_resolved(self):
        self.pair.write_store([
            thread("t1", "s", [user("do it", 100, 1), user("not quite", 300, 2)]),
        ])
        self.pair.write_journal([
            {"thread": "t1", "body": "Done.", "status": "resolved", "ts": 200, "turn": 1},
        ])
        r = self.pair.run()
        self.assertIn("1 threads, 1 need you", r.stdout)
        self.assertIn("[user turn 1] do it\n[agent] Done.\n[user turn 2] not quite\n", r.stdout)
        self.assertIn("t1  open  last=user", self.pair.run("--all").stdout)

    def test_status_only_resolve_after_user_message_stays_resolved(self):
        self.pair.write_store([thread("t1", "s", [user("do it", 100, 1)])])
        self.pair.write_journal([{"thread": "t1", "status": "resolved", "ts": 200, "turn": 1}])
        self.assertIn("0 need you", self.pair.run().stdout)
        self.assertIn("t1  resolved  last=user", self.pair.run("--all").stdout)

    # 4
    def test_agent_blocked_open_not_listed(self):
        self.pair.write_store([thread("t1", "s", [user("do it", 100, 1)])])
        self.pair.write_journal([
            {"thread": "t1", "body": "Which one?", "status": "open", "ts": 200, "turn": 1},
        ])
        self.assertIn("1 threads, 0 need you", self.pair.run().stdout)
        self.assertIn("t1  open  last=agent", self.pair.run("--all").stdout)

    # 5
    def test_image_thread_prints_src(self):
        self.pair.write_store([
            thread("t1", "the dock", [user("crop it", 1, 1)], src="assets/dock.png"),
        ])
        out = self.pair.run().stdout
        self.assertIn("anchor: the dock\nsrc: assets/dock.png\n[user turn 1] crop it\n", out)

    # 6
    def test_malformed_journal_line_skipped_with_warning(self):
        self.pair.write_store([thread("t1", "s", [user("do it", 100, 1)])])
        self.pair.write_journal([
            "{not json",
            {"thread": "t1", "body": "Done.", "status": "resolved", "ts": 200, "turn": 1},
        ])
        r = self.pair.run()
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stderr.count("warning:"), 1)
        self.assertIn("%s:1: malformed line skipped" % self.pair.journal, r.stderr)
        self.assertIn("0 need you", r.stdout)

    # 7
    def test_missing_journal_means_no_events(self):
        self.pair.write_store([thread("t1", "s", [user("do it", 100, 1)])])
        self.assertFalse(os.path.exists(self.pair.journal))
        r = self.pair.run()
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stderr, "")
        self.assertIn("1 threads, 1 need you\n=== t1", r.stdout)

    # 8
    def test_missing_store(self):
        r = self.pair.run()
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout, "no store yet: no threads\n")
        self.assertEqual(r.stderr, "")

    # 9
    def test_sweep_matches_rendered_text(self):
        self.pair.write_store([
            thread("t1", "The relay runs on a machine you own, and the config key is hubUrl.",
                   [user("a", 1, 1)]),
            thread("t2", "This sentence was deleted.", [user("b", 2, 1)]),
            thread("t3", "a dock", [user("c", 3, 1)], src="assets/dock.png"),
        ])
        self.pair.write_journal([{"thread": "t2", "body": "ok", "status": "resolved", "ts": 9, "turn": 1}])
        self.pair.write_doc(
            "# Title\n\n"
            "The **relay** runs on a [machine you\n"
            "own](https://example.com), and the config key is `hubUrl`.\n\n"
            "![a dock](assets/dock.png)\n")
        r = self.pair.run("--sweep", self.pair.doc)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout,
            "t2  resolved  This sentence was deleted.\n"
            "sweep: 1 of 2 anchors orphaned\n")

    # 10
    def test_sweep_uses_journal_anchor(self):
        self.pair.write_store([thread("t1", "old wording", [user("a", 1, 1)])])
        self.pair.write_doc("Some new wording here.\n")
        self.assertIn("t1  open  old wording\nsweep: 1 of 1", self.pair.run("--sweep", self.pair.doc).stdout)
        self.pair.write_journal([{"thread": "t1", "anchor": {"snippet": "new wording"}, "ts": 5, "turn": 1}])
        self.assertEqual(self.pair.run("--sweep", self.pair.doc).stdout, "sweep: 0 of 1 anchors orphaned\n")
        self.assertIn("anchor: new wording", self.pair.run().stdout)

    def test_usage_errors_exit_2(self):
        r = subprocess.run([sys.executable, TOOL], capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)
        r = subprocess.run([sys.executable, TOOL, "threads.json"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)
        self.pair.write_store([])
        r = self.pair.run("--sweep", os.path.join(os.path.dirname(self.pair.doc), "absent.md"))
        self.assertEqual(r.returncode, 2)


if __name__ == "__main__":
    unittest.main()
