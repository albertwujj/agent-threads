#!/usr/bin/env python3
"""List sent review threads with their diff anchors and conversation history."""
import argparse
import json
import math
import sys
from pathlib import Path

STORE_SUFFIX = "-comments.json"
JOURNAL_SUFFIX = "-agent.jsonl"
STATUSES = ("open", "resolved")
ANCHOR_STATUSES = ("ok", "moved", "lost")


def is_number(value):
    return type(value) is int or (type(value) is float and math.isfinite(value))


def is_user(message):
    return (message.get("author") or "user") == "user"


def journal_events(path):
    try:
        journal = path.open(encoding="utf-8")
    except FileNotFoundError:
        return
    with journal:
        for line_number, line in enumerate(journal, 1):
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except ValueError:
                event = None
            if not isinstance(event, dict) or not isinstance(event.get("thread"), str):
                print(f"warning: {path}:{line_number}: malformed event skipped", file=sys.stderr)
                continue
            yield event


def merge_sent_threads(store, events):
    threads = {}
    for thread in store["threads"]:
        if not isinstance(thread, dict) or not isinstance(thread.get("id"), str):
            continue
        thread_id = thread["id"]
        messages = [message for message in thread.get("messages") or []
                    if isinstance(message, dict)
                    and (not is_user(message) or is_number(message.get("turn")))]
        last_sent = next((message for message in reversed(messages) if is_user(message)), None)
        if last_sent is None:
            continue
        threads[thread_id] = {
            "id": thread_id,
            "title": thread.get("title") or "",
            "anchor": dict(thread.get("anchor") or {}),
            "anchor_status": thread.get("anchor_status"),
            "messages": messages,
            "last_sent_ts": last_sent.get("ts"),
            "status": None,
            "status_ts": 0,
        }

    for event in events:
        thread_id = event["thread"]
        thread = threads.get(thread_id)
        if thread is None:
            continue
        body = event.get("body")
        if isinstance(body, str) and body.strip():
            thread["messages"].append({"author": "agent", "body": body,
                                       "ts": event.get("ts"), "turn": event.get("turn")})
        if event.get("status") in STATUSES:
            thread["status"] = event["status"]
            timestamp = event.get("ts")
            if is_number(timestamp):
                thread["status_ts"] = max(thread["status_ts"], timestamp)
        if isinstance(event.get("title"), str):
            thread["title"] = event["title"]
        if isinstance(event.get("anchor"), dict):
            thread["anchor"].update(event["anchor"])
        if event.get("anchor_status") in ANCHOR_STATUSES:
            thread["anchor_status"] = event["anchor_status"]

    for thread in threads.values():
        # Drafts must neither reopen a thread nor displace its last sent request.
        timestamp = thread["last_sent_ts"]
        if is_number(timestamp) and timestamp > thread["status_ts"]:
            thread["status"] = None
    return list(threads.values())


def message_time(message):
    timestamp = message.get("ts")
    return timestamp if is_number(timestamp) else math.inf


def print_thread(thread):
    status = {None: "needs agent", "open": "blocked on user", "resolved": "resolved"}
    title = f" {thread['title']}" if thread["title"] else ""
    print(f"=== {thread['id']} [{status[thread['status']]}]{title}")
    anchor = thread["anchor"]
    for field in ("path", "side", "line", "heading", "snippet", "context"):
        value = anchor.get(field)
        if value is not None and value != "":
            print(f"{field}: {value}")
    if thread["anchor_status"]:
        print(f"anchor status: {thread['anchor_status']}")
    for message in sorted(thread["messages"], key=message_time):
        author = message.get("author") or "user"
        turn = message.get("turn")
        label = f"{author} turn {turn}" if is_number(turn) else author
        print(f"[{label}] {message.get('body') or ''}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("store", type=Path, help="path to the review's -comments.json file")
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument("--all", action="store_true", help="show every sent thread")
    selection.add_argument("--thread", metavar="ID", help="show a single sent thread")
    args = parser.parse_args()
    if not args.store.name.endswith(STORE_SUFFIX):
        parser.error("store path must end in " + STORE_SUFFIX)

    try:
        store = json.loads(args.store.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print("no store yet: no review threads")
        return 0
    except (OSError, ValueError) as error:
        print(f"{args.store}: {error}", file=sys.stderr)
        return 1
    if not isinstance(store, dict) or not isinstance(store.get("threads"), list):
        print(f"{args.store}: not a thread store", file=sys.stderr)
        return 1

    journal = args.store.with_name(args.store.name[:-len(STORE_SUFFIX)] + JOURNAL_SUFFIX)
    try:
        threads = merge_sent_threads(store, journal_events(journal))
    except (OSError, UnicodeError) as error:
        print(f"{journal}: {error}", file=sys.stderr)
        return 1

    pending = [thread for thread in threads if thread["status"] is None]
    print(f"store: {args.store}  {len(threads)} sent threads, {len(pending)} need you")
    if args.thread is not None:
        selected = [thread for thread in threads if thread["id"] == args.thread]
        if not selected:
            print(f"no sent thread matches {args.thread}")
    else:
        selected = threads if args.all else pending
    for thread in selected:
        print()
        print_thread(thread)
    return 0


if __name__ == "__main__":
    sys.exit(main())
