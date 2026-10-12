#!/usr/bin/env python3
"""Tests for journal.py. From the repo root:

    python3 -m unittest discover -s .maintainer/tests
"""
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOL = os.path.join(REPO, "journal.py")
OPEN_THREADS = os.path.join(REPO, "md", "open-threads.py")


class JournalTest(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = os.path.join(self.tmp.name, "doc-comments.json")
        self.journal = os.path.join(self.tmp.name, "doc-agent.jsonl")
        with open(self.store, "w", encoding="utf-8") as f:
            json.dump({"version": 1, "turn": 4, "threads": [
                {"id": "t1", "anchor": {"snippet": "old words", "heading": "Intro"},
                 "messages": [{"author": "user", "body": "fix it", "ts": 1, "turn": 4}]},
                {"id": "t2", "anchor": {"snippet": "old words"},
                 "messages": [{"author": "user", "body": "and this", "ts": 1, "turn": 4}]},
            ]}, f)

    def tearDown(self):
        self.tmp.cleanup()

    def run_tool(self, *args, stdin=None):
        return subprocess.run([sys.executable, TOOL, self.store] + list(args),
                              capture_output=True, text=True, input=stdin)

    def lines(self):
        if not os.path.exists(self.journal):
            return []
        with open(self.journal, encoding="utf-8") as f:
            return [json.loads(line) for line in f]

    def test_reply_is_stamped_with_time_and_turn(self):
        before = time.time_ns() // 1_000_000
        r = self.run_tool("reply", "t1", "Tightening it: the clause repeats.")
        self.assertEqual(r.returncode, 0, r.stderr)
        [event] = self.lines()
        self.assertEqual(event["thread"], "t1")
        self.assertEqual(event["body"], "Tightening it: the clause repeats.")
        self.assertEqual(event["turn"], 4)
        self.assertGreaterEqual(event["ts"], before)
        self.assertNotIn("status", event)

    def test_resolve_with_and_without_words(self):
        self.run_tool("resolve", "t1")
        self.run_tool("resolve", "t2", "Answered: yes.")
        first, second = self.lines()
        self.assertEqual(first, {"thread": "t1", "status": "resolved", "ts": first["ts"], "turn": 4})
        self.assertEqual(second["body"], "Answered: yes.")
        self.assertEqual(second["status"], "resolved")

    def test_block_carries_the_question_and_the_open_status(self):
        self.run_tool("block", "t1", "Which of the two?")
        [event] = self.lines()
        self.assertEqual((event["body"], event["status"]), ("Which of the two?", "open"))

    def test_text_from_stdin_keeps_quotes(self):
        text = 'Using "now" and it\'s shorter.\nSecond line.'
        r = self.run_tool("reply", "t1", "-", stdin=text + "\n")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.lines()[0]["body"], text)

    def test_anchor_repoints_several_threads_in_one_write(self):
        r = self.run_tool("anchor", "t1", "t2", "--snippet", "new words", "--heading", "Intro")
        self.assertEqual(r.returncode, 0, r.stderr)
        events = self.lines()
        self.assertEqual([e["thread"] for e in events], ["t1", "t2"])
        self.assertEqual(events[0]["anchor"], {"snippet": "new words", "heading": "Intro"})
        self.assertEqual(events[0]["ts"], events[1]["ts"])

    def test_review_anchor_fields(self):
        self.run_tool("anchor", "t1", "--snippet", "if x:", "--path", "src/a.py",
                      "--side", "new", "--line", "42")
        self.assertEqual(self.lines()[0]["anchor"],
                         {"snippet": "if x:", "path": "src/a.py", "side": "new", "line": "42"})

    def test_title(self):
        self.run_tool("title", "t1", "Tighten wording")
        self.assertEqual(self.lines()[0]["title"], "Tighten wording")

    def test_unknown_thread_fails_and_writes_nothing(self):
        r = self.run_tool("anchor", "t1", "t9", "--snippet", "x")
        self.assertEqual(r.returncode, 1)
        self.assertIn("t9", r.stderr)
        self.assertEqual(self.lines(), [])

    def test_missing_store_fails_and_is_never_created(self):
        os.remove(self.store)
        r = self.run_tool("reply", "t1", "hi")
        self.assertEqual(r.returncode, 1)
        self.assertFalse(os.path.exists(self.store))
        self.assertFalse(os.path.exists(self.journal))

    def test_usage_errors(self):
        self.assertEqual(self.run_tool("reply", "t1", "   ").returncode, 2)
        self.assertEqual(self.run_tool("anchor", "t1", "--snippet", "x", "--line", "4a").returncode, 2)
        self.assertEqual(self.run_tool("block", "t1").returncode, 2)
        self.assertEqual(subprocess.run([sys.executable, TOOL, os.path.join(self.tmp.name, "doc.md"), "resolve", "t1"],
                                        capture_output=True).returncode, 2)

    def test_what_it_writes_reads_back_through_the_merge(self):
        self.run_tool("reply", "t1", "Doing it.")
        self.run_tool("resolve", "t1")
        self.run_tool("block", "t2", "Which?")
        r = subprocess.run([sys.executable, OPEN_THREADS, self.store, "--all"], capture_output=True, text=True)
        self.assertIn("t1  resolved", r.stdout)
        self.assertIn("t2  open", r.stdout)
        self.assertIn("0 need you", r.stdout)


if __name__ == "__main__":
    unittest.main()
