# The thread store (shared contract)

One thread model carries the human↔agent conversation on two surfaces: a
**review package** (see `code/produce-review.md`) and a **live markdown
document** (see `md/user-intent.md`). Each conversation is a pair of files;
where they live is surface-specific and defined in each runbook. This doc is
the shared contract: the files, the schema, the event rules, and the status
lifecycle.

## Two files, one writer each

- `<stem>-comments.json` — the **store**: threads, the user's messages,
  anchors. The viewer writes it; you only read it.
- `<stem>-agent.jsonl` — your **journal**, beside the store: everything you
  say or set, appended one JSON object per line. You are its only writer. It
  may not exist yet; your first append creates it.

A thread's truth is the store with the journal applied in file order. Every
reader, the viewer included, merges the two at read time, so an append is all
it takes for your reply to surface. Always read both files: your own
resolutions live only in the journal.

**What needs you:** every thread that is `open` after the merge whose last
message is the user's. The last-message test settles both edge cases: a
thread where you replied and set `open` (blocked) has your word last, so it
waits on the user, not you; a `resolved` thread with a newer user message
under it is reopened and needs you again.

## Store schema (you read, never write)

```jsonc
{ "version": 1,
  "turn": 4,                     // logical clock: count of user send-batches;
                                 // the viewer ticks it, you stamp it on events
  "threads": [
  { "id": "t…",
    "title": "",                 // short intent summary; you set it (see Titles)
    "anchor": {
      "snippet": "if tokens <= 0:",  // the real anchor: exact text on the surface
      "context": ""                  // only when snippet is short/repeated: the
    },                               // enclosing line or paragraph it sits in
    "anchor_status": "ok",       // ok | moved | lost — review stamps it;
                                 // markdown doesn't (it anchors by snippet live)
    "status": "open",            // legacy stores only (pre-journal, agent-
                                 // written); absent in new stores — effective
                                 // status comes from the merge, absent = open
    "messages": [ { "author": "user", "body": "…", "ts": 1719500000000, "turn": 4 } ]
  } ] }
```

Surfaces extend the anchor: review code anchors add `path`/`side`/`line`;
markdown anchors add `heading`, and a markdown comment on an **image** adds
`src` (the image's authored path) with `snippet` holding the image's alt text
as a label — read it as a comment on that image, and update `src` if you move
or replace it. `title` and the `turn` fields are optional and absent in older
stores. Older stores may also carry your messages inline in `messages` —
still valid to read; new replies go to the journal only.

## Journal events

One line per action, appended to `<stem>-agent.jsonl`:

```jsonc
{ "thread": "t…",               // required: the store thread id
  "body": "…",                  // a reply on that thread
  "status": "resolved",         // or "open" — see Status lifecycle
  "title": "…",                 // set/replace the thread's title (review)
  "anchor": { "snippet": "…" }, // fields merged into the thread's anchor
  "ts": 1719500000000,          // real epoch ms (`date +%s%3N`), never invented
  "turn": 4 }                   // the store's current `turn`, read at write time
```

One event may carry several fields — a reply plus its `"status":"resolved"`
is one line.

- **Append per thread, as you finish it** — never one batch at the end. Each
  append streams into the open viewer while you work.
- Append only. Correct yourself with a further event (later lines win);
  never rewrite the journal, and never write the store file at all.
- Stamp `ts` and `turn` on every event.
- Keep anchors current: when your own edit changes the anchored text, append
  an `anchor` event updating `snippet` (and surface-specific fields) so the
  thread stays placed.
- When every open thread has its disposition, the turn is over: no further
  journal writes until the user's next send.

## Status lifecycle

Shared on both surfaces: a user follow-up reopens a thread to `open` — the
follow-up IS the reopen, there is no separate action. The store-level `turn`
is the viewer's alone; read it and stamp it on your events, never change it.

### Blocked, or done

Every thread you work ends in exactly one of two states, and you set it (a
`status` event) — the same on both surfaces:

- `resolved` — you completed the user's ask. Nothing is needed from them.
- `open` — you are **blocked**: you cannot finish without the user. Your reply
  must say exactly what you need.

**Replying is not resolving.** A reply that answers the question and needs
nothing back is `resolved`. There is no `read` and no `answered`: "I said
something" is not a state the user can act on, and only you know whether their
ask is actually done. That is the whole reason this is yours to set — nothing
else in the system can see it.

Be honest about blocking. An `open` thread is the user's worklist and the
viewer spends its attention there, while everything resolved folds away. A
thread left `open` without a real blocker costs the user attention they cannot
ignore; one resolved without doing the work hides a failure they were trusting
you to report.

This is yours alone on both surfaces. The user never closes a thread — they
comment, and a follow-up reopens it. So `resolved` always means you said the
work was done.

**Resolve after the work is visible.** Each surface shows work on its own
clock: markdown renders the saved document, review renders the committed
range. Set `resolved` only once the change it claims is already in front of
the user — on markdown after the document write, on review after the commit.
The fold is the user's receipt that the final state is on screen.

## Titles (review only)

When a thread's `title` is empty, set it while working the thread: a `title`
event with a short intent summary (a few words, e.g. "Tighten polling
wording"). Threads born from user edits especially need one — their first
message is a diff, which makes a poor label. The review viewer shows the
title on the collapsed thread line.

The markdown viewer shows no per-thread label — an open thread renders its
messages, and resolved ones collapse into a count — so skip titles there.

## What the user sees (viewer behavior, for your awareness)

On **markdown**, an `open` thread renders in full: it is blocking you, so it
gets the only space on the page. Every `resolved` thread under a block
collapses together into a single line — the newest one's opening ask, plus
"+N more" for the rest — which the user can unfold. Your
work is already visible as the document change itself, so a resolved reply is
supporting detail rather than something the user must read. This is why the
two states have to be honest: they are the only signal deciding what takes
the user's attention.

On **review**, a `resolved` thread collapses to a one-line disclosure the user
can click open; `open` threads never fold. Same rule as markdown, different
shape: what you finished gets out of the way, what you are blocked on stays in
front of them.

If you go quiet with sent threads still lacking a disposition, the host
re-pings you once with a reminder naming the store — treat it exactly like
the original send.

## Handing back

After working the threads, tell the user in the terminal only that you did,
briefly (a count, or one line across all threads). Your per-thread replies
already render inline on the surface; restating them makes the user read
everything twice.
