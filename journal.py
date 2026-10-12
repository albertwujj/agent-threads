#!/usr/bin/env python3
"""Write to a thread journal: your replies, statuses, anchors and titles.

    python3 journal.py STORE reply   THREAD TEXT
    python3 journal.py STORE resolve THREAD [TEXT]
    python3 journal.py STORE block   THREAD TEXT
    python3 journal.py STORE anchor  THREAD [THREAD ...] --snippet TEXT
                       [--context TEXT] [--heading TEXT] [--src PATH]
                       [--path PATH] [--side old|new] [--line N]
    python3 journal.py STORE title   THREAD TEXT

STORE is the NAME-comments.json path; the journal is NAME-agent.jsonl beside
it. TEXT given as - is read from stdin. Each call appends its events in one
write, stamped with the time and the store's current turn.

  reply    your words on the thread, ahead of the change they explain
  resolve  done: the status, with your words when TEXT is given
  block    blocked on the user: your question and the open status
  anchor   repoint the threads at their passage's current text
  title    the thread's short label (review)

Exit 0 on success, 1 when the store or a thread is not usable, 2 on usage
error.
"""
import argparse
import json
import os
import sys
import time

STORE_SUFFIX = "-comments.json"
JOURNAL_SUFFIX = "-agent.jsonl"


def fail(msg, code=1):
    sys.stderr.write("journal.py: %s\n" % msg)
    sys.exit(code)


def text_arg(value, what):
    text = sys.stdin.read() if value == "-" else value
    text = text.strip()
    if not text:
        fail("%s is empty" % what, 2)
    return text


def read_store(path):
    if not path.endswith(STORE_SUFFIX):
        fail("%s is not a NAME%s store" % (path, STORE_SUFFIX), 2)
    if not os.path.exists(path):
        fail("%s does not exist: the viewer creates the store, never you" % path)
    try:
        with open(path, encoding="utf-8") as f:
            store = json.load(f)
    except (OSError, ValueError) as e:
        fail("cannot read %s: %s" % (path, e))
    if not isinstance(store, dict) or not isinstance(store.get("threads"), list):
        fail("%s is not a thread store" % path)
    return store


def parse(argv):
    p = argparse.ArgumentParser(prog="journal.py", add_help=True)
    p.add_argument("store")
    sub = p.add_subparsers(dest="action", required=True)
    for name in ("reply", "block", "title"):
        s = sub.add_parser(name)
        s.add_argument("thread")
        s.add_argument("text")
    s = sub.add_parser("resolve")
    s.add_argument("thread")
    s.add_argument("text", nargs="?")
    s = sub.add_parser("anchor")
    s.add_argument("threads", nargs="+")
    s.add_argument("--snippet", required=True)
    s.add_argument("--context")
    s.add_argument("--heading")
    s.add_argument("--src")
    s.add_argument("--path")
    s.add_argument("--side", choices=("old", "new"))
    s.add_argument("--line")
    try:
        return p.parse_args(argv)
    except SystemExit as e:
        sys.exit(2 if e.code else 0)


def events(args):
    if args.action == "reply":
        return [{"thread": args.thread, "body": text_arg(args.text, "the reply")}]
    if args.action == "resolve":
        event = {"thread": args.thread}
        if args.text is not None:
            event["body"] = text_arg(args.text, "the reply")
        event["status"] = "resolved"
        return [event]
    if args.action == "block":
        return [{"thread": args.thread, "body": text_arg(args.text, "what you need"),
                 "status": "open"}]
    if args.action == "title":
        return [{"thread": args.thread, "title": text_arg(args.text, "the title")}]
    anchor = {"snippet": text_arg(args.snippet, "the snippet")}
    for key in ("context", "heading", "src", "path", "side"):
        value = getattr(args, key)
        if value is not None:
            anchor[key] = value
    if args.line is not None:
        if not args.line.isdigit():
            fail("--line must be a line number", 2)
        anchor["line"] = args.line
    return [{"thread": t, "anchor": dict(anchor)} for t in args.threads]


def main(argv):
    args = parse(argv)
    store = read_store(args.store)
    known = {t.get("id") for t in store["threads"] if isinstance(t, dict)}
    out = events(args)
    unknown = sorted({e["thread"] for e in out} - known)
    if unknown:
        fail("no such thread in the store: %s" % ", ".join(unknown))
    ts = time.time_ns() // 1_000_000
    turn = store.get("turn")
    lines = []
    for event in out:
        event["ts"] = ts
        if isinstance(turn, int):
            event["turn"] = turn
        lines.append(json.dumps(event, ensure_ascii=False) + "\n")
    journal = args.store[:-len(STORE_SUFFIX)] + JOURNAL_SUFFIX
    with open(journal, "a", encoding="utf-8") as f:
        f.write("".join(lines))
    for event in out:
        print("%s %s" % (args.action, event["thread"]))


if __name__ == "__main__":
    main(sys.argv[1:])
