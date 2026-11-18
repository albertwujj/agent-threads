import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


TOOL = Path(__file__).resolve().parents[2] / "code" / "open-threads.py"


def user(body, ts, turn=None):
    message = {"author": "user", "body": body, "ts": ts}
    if turn is not None:
        message["turn"] = turn
    return message


def review_thread(thread_id, *messages):
    return {
        "id": thread_id,
        "title": "Check the return value",
        "anchor": {"path": "src/example.py", "side": "old", "line": "17",
                   "snippet": "return result", "context": "The fallback branch"},
        "anchor_status": "lost",
        "messages": list(messages),
    }


class ReviewOpenThreadsTest(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.store = Path(directory.name) / "topic-comments.json"
        self.journal = self.store.with_name("topic-agent.jsonl")

    def write_store(self, *threads):
        self.store.write_text(json.dumps({"version": 1, "turn": 3, "threads": threads}),
                              encoding="utf-8")

    def write_journal(self, *events):
        self.journal.write_text("".join(json.dumps(event) + "\n" for event in events),
                                encoding="utf-8")

    def listing(self, *args):
        result = subprocess.run([sys.executable, str(TOOL), str(self.store), *args],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def test_pending_listing_hides_drafts_and_keeps_the_sent_request(self):
        self.write_store(
            review_thread("sent", user("Check the fallback", 100, 1), user("Draft follow-up", 300)),
            review_thread("draft", user("Draft-only comment", 200)),
        )
        output = self.listing().stdout
        self.assertIn("1 sent threads, 1 need you", output)
        self.assertIn("=== sent [needs agent] Check the return value", output)
        self.assertIn("path: src/example.py\nside: old\nline: 17", output)
        self.assertIn("snippet: return result\ncontext: The fallback branch\nanchor status: lost", output)
        self.assertIn("[user turn 1] Check the fallback", output)
        self.assertNotIn("Draft", self.listing("--all").stdout)
        self.assertNotIn("Draft", output)
        self.assertIn("no sent thread matches draft", self.listing("--thread", "draft").stdout)
        self.assertFalse(self.journal.exists())

    def test_resolved_and_blocked_only_show_in_sent_history(self):
        self.write_store(
            review_thread("done", user("Close this", 100, 1), user("Unsent change of mind", 300)),
            review_thread("blocked", user("Which input?", 100, 1)),
        )
        self.write_journal(
            {"thread": "done", "status": "resolved", "ts": 200},
            {"thread": "blocked", "status": "open", "body": "Please attach the input.", "ts": 200},
        )
        output = self.listing().stdout
        self.assertIn("2 sent threads, 0 need you", output)
        self.assertNotIn("===", output)
        history = self.listing("--all").stdout
        self.assertIn("=== done [resolved]", history)
        self.assertIn("=== blocked [blocked on user]", history)
        self.assertNotIn("Unsent change of mind", history)
        one_thread = self.listing("--thread", "done").stdout
        self.assertIn("=== done [resolved]", one_thread)
        self.assertNotIn("=== blocked", one_thread)

    def test_sent_follow_up_reopens_and_preserves_full_conversation(self):
        self.write_store(review_thread("t1", user("First request", 100, 1),
                                       user("[Confirm] Decision: Keep the fallback", 300, 2)))
        self.write_journal(
            {"thread": "t1", "status": "resolved", "body": "First reply", "ts": 200, "turn": 1},
            {"thread": "t1", "body": "I will update the heading", "ts": 400, "turn": 2},
        )
        output = self.listing().stdout
        self.assertIn("=== t1 [needs agent]", output)
        self.assertIn("[user turn 1] First request\n"
                      "[agent turn 1] First reply\n"
                      "[user turn 2] [Confirm] Decision: Keep the fallback\n"
                      "[agent turn 2] I will update the heading\n", output)

    def test_anchor_and_title_events_merge_in_order_and_torn_append_is_skipped(self):
        edit = "[Edit]\n<del>Old</del><ins>New</ins> message\n[/Edit]"
        item = review_thread("t1", user(edit, 100, 1))
        item["anchor"] = {"path": "(commit message)", "snippet": "Old message"}
        self.write_store(item)
        self.write_journal(
            {"thread": "discarded", "body": "Earlier thread"},
            {"thread": "t1", "title": "Improve commit wording", "anchor": {"snippet": "New message"}},
            {"thread": "t1", "anchor": {"heading": "Commit"}, "anchor_status": "moved"},
        )
        with self.journal.open("a", encoding="utf-8") as handle:
            handle.write('{"thread":')
        before = (self.store.read_bytes(), self.journal.read_bytes())
        result = self.listing()
        self.assertIn("warning:", result.stderr)
        self.assertIn("=== t1 [needs agent] Improve commit wording", result.stdout)
        self.assertIn("path: (commit message)\nheading: Commit\nsnippet: New message", result.stdout)
        self.assertIn("anchor status: moved", result.stdout)
        self.assertIn(edit, result.stdout)
        self.assertNotIn("Earlier thread", result.stdout)
        self.assertEqual((self.store.read_bytes(), self.journal.read_bytes()), before)

    def test_missing_store_does_not_create_files(self):
        self.assertIn("no review threads", self.listing().stdout)
        self.assertFalse(self.store.exists())
        self.assertFalse(self.journal.exists())
