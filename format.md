# Store and journal format

The two files of a conversation, line by line: what the host writes, what
`journal.py` writes, and how every reader merges them. An agent writes the
journal by hand only when the user has asked for that (`troubleshooting.md`).

## Store: `<stem>-comments.json` (the host writes it)

```jsonc
{ "version": 1,
  "turn": 4,                     // logical clock: count of user send-batches;
                                 // the host ticks it, the agent stamps it on events
  "threads": [
  { "id": "t…",
    "title": "",                 // short intent summary; the agent sets it (review)
    "anchor": {
      "snippet": "if tokens <= 0:",  // exact text on the surface
      "context": ""                  // only when snippet is short/repeated
    },
    "anchor_status": "ok",       // ok | moved | lost — review stamps it;
                                 // markdown anchors by snippet live
    "messages": [ { "author": "user", "body": "…", "ts": 1719500000000, "turn": 4 } ]
  } ] }
```

Anchors carry the surface fields in `contract.md` (Anchors). A user message
carries `turn` once a send has handed it to the agent; a review draft the
user has not sent has none. There is no `status` field in the store.

## Journal: `<stem>-agent.jsonl` (the agent writes it)

One JSON object per line, appended:

```jsonc
{ "thread": "t…",               // required: the store thread id
  "body": "…",                  // a reply on that thread
  "status": "resolved",         // or "open" (blocked on the user)
  "title": "…",                 // the thread's title (review)
  "anchor": { "snippet": "…" }, // fields merged into the thread's anchor
  "ts": 1719500000000,          // real epoch milliseconds, at write time
  "turn": 4 }                   // the store's current `turn`, read at write time
```

One event may carry several fields; a reply with its status is one line.
Write each line whole, in one append, and never edit earlier lines. For `ts`,
`date +%s%3N` works on Linux; on macOS use
`perl -MTime::HiRes=time -e 'printf "%d\n", time*1000'`. The thread id must
be one the store holds.

## The merge

A thread's truth is the store thread with its journal events applied in file
order: a `body` becomes an agent message, placed among the user's messages
by `ts`; later `status`, `title` and `anchor` fields win. A torn final line,
and an event for a thread the store no longer holds, are skipped.

A status answers the user's last message. A user message newer than the
status (by `ts`) takes it back: the thread is open and needs the agent again,
even after the agent replies, until a new status. A status without `ts`
counts as older than any timestamped user message.
