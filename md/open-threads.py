#!/usr/bin/env python3
"""List the markdown document threads that need you.

    python3 open-threads.py <path/to/NAME-comments.json> [--sweep <path/to/NAME.md>] [--all]

Reads the store and the journal beside it (NAME-agent.jsonl), merges them
per ../contract.md, and prints the threads that are open with the user's
message last, each with its anchor and its full message history.

  --all            one line per thread: id, status, whose message is last,
                   heading, snippet
  --sweep NAME.md  after your edits: print the threads whose snippet no
                   longer appears in an approximation of the rendered text

Reads only; never writes. Exit 0 on success, 2 on usage error.
"""
import json
import os
import re
import sys

USAGE = ("usage: open-threads.py <path/to/NAME-comments.json> "
         "[--sweep <path/to/NAME.md>] [--all]")
STORE_SUFFIX = "-comments.json"
JOURNAL_SUFFIX = "-agent.jsonl"
SHORT_SNIPPET = 60   # below this, the context line is printed too
ALL_SNIPPET = 80     # --all truncates snippets to this


def warn(msg):
    sys.stderr.write("warning: %s\n" % msg)


def usage_error(msg):
    sys.stderr.write("%s\n%s\n" % (msg, USAGE))
    sys.exit(2)


def ts_of(obj):
    ts = obj.get("ts")
    return ts if isinstance(ts, (int, float)) else 0


def collapse(text):
    return re.sub(r"\s+", " ", text).strip()


# --- reading ------------------------------------------------------------

def read_store(path):
    with open(path, encoding="utf-8") as f:
        store = json.load(f)
    if not isinstance(store, dict) or not isinstance(store.get("threads"), list):
        sys.stderr.write("%s: not a thread store\n" % path)
        sys.exit(1)
    return store


def read_journal(path):
    """Well-formed events in file order, as (line_no, event). A malformed
    line is skipped with a warning; a missing journal has no events."""
    events = []
    if not os.path.exists(path):
        return events
    with open(path, encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                ev = json.loads(line)
            except ValueError:
                ev = None
            if not isinstance(ev, dict) or not isinstance(ev.get("thread"), str):
                warn("%s:%d: malformed line skipped" % (path, n))
                continue
            events.append((n, ev))
    return events


# --- merge (contract.md) ------------------------------------------------

def merge(store, events, journal_path):
    """A thread's truth is the store thread with its journal events applied
    in file order. Every thread is open until an event sets a status; a
    user message newer than a `resolved` reopens it."""
    threads = []
    by_id = {}
    for t in store["threads"]:
        if not isinstance(t, dict):
            continue
        thread = {
            "id": str(t.get("id", "")),
            "anchor": dict(t.get("anchor") or {}),
            "messages": [],
            "journal_status": None,
            "status_ts": 0,
        }
        for m in t.get("messages") or []:
            if isinstance(m, dict):
                thread["messages"].append({
                    "author": m.get("author") or "user",
                    "body": m.get("body") or "",
                    "ts": ts_of(m),
                    "turn": m.get("turn"),
                })
        threads.append(thread)
        by_id[thread["id"]] = thread

    # Events for threads the viewer has since discarded are normal on a
    # long-lived store (the journal is append-only); count them, one line.
    gone = {}
    for n, ev in events:
        thread = by_id.get(ev["thread"])
        if thread is None:
            gone[ev["thread"]] = gone.get(ev["thread"], 0) + 1
            continue
        if isinstance(ev.get("anchor"), dict):
            thread["anchor"].update(ev["anchor"])
        if isinstance(ev.get("status"), str):
            thread["journal_status"] = ev["status"]
            thread["status_ts"] = ts_of(ev)
        if isinstance(ev.get("body"), str) and ev["body"]:
            thread["messages"].append({
                "author": "agent",
                "body": ev["body"],
                "ts": ts_of(ev),
                "turn": ev.get("turn"),
            })

    if gone:
        warn("%s: %d events for %d threads no longer in the store, skipped"
             % (journal_path, sum(gone.values()), len(gone)))

    for thread in threads:
        msgs = thread["messages"]
        msgs.sort(key=lambda m: m["ts"])  # stable: store order, then journal order, on ties
        status = thread["journal_status"] or "open"
        if status == "resolved" and any(
                m["author"] == "user" and m["ts"] > thread["status_ts"] for m in msgs):
            status = "open"
        thread["status"] = status
        thread["last"] = msgs[-1]["author"] if msgs else "none"
        thread["needs"] = status == "open" and thread["last"] == "user"
    return threads


# --- listing ------------------------------------------------------------

def print_header(path, store, threads):
    turn = store.get("turn")
    need = sum(1 for t in threads if t["needs"])
    print("store: %s  turn %s  %d threads, %d need you" % (
        path, turn if turn is not None else "-", len(threads), need))


def print_needing(threads):
    first = True
    for t in threads:
        if not t["needs"]:
            continue
        if not first:
            print()
        first = False
        a = t["anchor"]
        heading = a.get("heading") or ""
        print("=== %s  heading: %s" % (t["id"], heading) if heading else "=== %s" % t["id"])
        snippet = a.get("snippet") or ""
        print("anchor: %s" % snippet)
        if a.get("src"):
            print("src: %s" % a["src"])
        context = a.get("context") or ""
        if len(snippet) < SHORT_SNIPPET and context:
            print("context: %s" % context)
        for m in t["messages"]:
            if m["author"] == "user" and m["turn"] is not None:
                label = "[user turn %s]" % m["turn"]
            else:
                label = "[%s]" % m["author"]
            print("%s %s" % (label, m["body"]))


def print_all(threads):
    for t in threads:
        a = t["anchor"]
        snippet = collapse(a.get("snippet") or "")
        if len(snippet) > ALL_SNIPPET:
            snippet = snippet[:ALL_SNIPPET - 1] + "…"
        print("%s  %s  last=%s  %s | %s" % (
            t["id"], t["status"], t["last"], a.get("heading") or "", snippet))


# --- sweep --------------------------------------------------------------

FENCE = re.compile(r"^\s{0,3}(```|~~~)")
RULE_ROW = re.compile(r"^(?=.*-)[\s|:\-]+$")      # |---|:--:| rows, horizontal rules
BLOCKQUOTE = re.compile(r"^\s*(>\s?)+")
HEADING = re.compile(r"^\s{0,3}#{1,6}\s+")
LIST_MARKER = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")
IMAGE = re.compile(r"!\[([^\]]*)\]\([^)]*\)")
LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")
HTML_TAG = re.compile(r"<[^<>]+>")
EMPHASIS_OPEN = re.compile(r"(?<!\w)[*_](?=\w)")
EMPHASIS_CLOSE = re.compile(r"(?<=\w)[*_](?!\w)")


def render(markdown):
    """Approximate the viewer's rendered text: markup stripped, fenced code
    kept verbatim, all whitespace collapsed. The viewer's own matching is
    the truth; this is a cheap first pass."""
    parts = []
    prose = []
    in_fence = False

    def flush():
        if prose:
            parts.append(render_inline("\n".join(prose)))
            del prose[:]

    for line in markdown.splitlines():
        if FENCE.match(line):
            flush()
            in_fence = not in_fence
            continue
        if in_fence:
            parts.append(line)
        else:
            prose.append(render_block_line(line))
    flush()
    return collapse("\n".join(parts))


def render_block_line(line):
    """Line-level markup: headings, list markers, blockquotes, table rules."""
    if RULE_ROW.match(line):
        return ""
    line = BLOCKQUOTE.sub("", line)
    line = HEADING.sub("", line)
    return LIST_MARKER.sub("", line)


def render_inline(text):
    """Inline markup over a whole prose run, so a link or emphasis that
    wraps across source lines still flattens."""
    text = IMAGE.sub(r"\1", text)
    text = LINK.sub(r"\1", text)
    text = HTML_TAG.sub("", text)
    text = text.replace("`", "").replace("**", "").replace("__", "")
    text = EMPHASIS_OPEN.sub("", text)
    text = EMPHASIS_CLOSE.sub("", text)
    return text.replace("|", " ")


def sweep(threads, doc_path):
    with open(doc_path, encoding="utf-8") as f:
        rendered = render(f.read())
    checked = orphaned = 0
    for t in threads:
        a = t["anchor"]
        if a.get("src"):
            continue  # an image thread is placed by src, not by text
        checked += 1
        snippet = collapse(a.get("snippet") or "")
        if snippet and snippet in rendered:
            continue
        orphaned += 1
        print("%s  %s  %s" % (t["id"], t["status"], snippet))
    print("sweep: %d of %d anchors orphaned" % (orphaned, checked))


# --- main ---------------------------------------------------------------

def main(argv):
    store_path = None
    doc_path = None
    show_all = False
    args = list(argv)
    while args:
        a = args.pop(0)
        if a in ("-h", "--help"):
            print(__doc__.strip())
            return 0
        if a == "--all":
            show_all = True
        elif a == "--sweep":
            if not args:
                usage_error("--sweep needs a document path")
            doc_path = args.pop(0)
        elif a.startswith("-"):
            usage_error("unknown option: " + a)
        elif store_path is None:
            store_path = a
        else:
            usage_error("unexpected argument: " + a)
    if store_path is None:
        usage_error("missing store path")
    if not store_path.endswith(STORE_SUFFIX):
        usage_error("store path must end in " + STORE_SUFFIX)
    if doc_path is not None and not os.path.isfile(doc_path):
        usage_error("no such document: " + doc_path)
    if not os.path.exists(store_path):
        print("no store yet: no threads")
        return 0

    journal_path = store_path[:-len(STORE_SUFFIX)] + JOURNAL_SUFFIX
    store = read_store(store_path)
    threads = merge(store, read_journal(journal_path), journal_path)

    if doc_path is None or show_all:
        print_header(store_path, store, threads)
        if show_all:
            print_all(threads)
        else:
            print_needing(threads)
    if doc_path is not None:
        if show_all:
            print()
        sweep(threads, doc_path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
