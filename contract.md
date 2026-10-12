# The thread store (shared contract)

One thread model carries the human↔agent conversation on two surfaces: a
**review package** (see `code/produce-review.md`) and a **live markdown
document** (see `md/user-intent.md`). Each conversation is a pair of files;
where they live is surface-specific and defined in each runbook. This doc is
the shared contract: the files, how you write to them, and the status
lifecycle. If a helper here fails, see `troubleshooting.md`.

## Two files, one writer each

- `<stem>-comments.json` — the **store**: threads, the user's messages,
  anchors. The viewer writes it; you only read it.
- `<stem>-agent.jsonl` — your **journal**, beside the store: everything you
  say or set. You are its only writer, through `journal.py` (below). It may
  not exist yet; your first write creates it.

A thread's truth is the store with the journal applied in order. Every
reader, the viewer included, merges the two at read time, so a write is all
it takes for your reply to surface. Your own statuses live only in the
journal; each surface's tool reads the two together.

**What needs you:** every thread you have set no status on since the user's
last message. A thread you set `open` (blocked) waits on the user, not you; a
user message newer than your status, `resolved` or `open`, reopens the thread
and it needs you again; a reply with no status after it still needs you.

## Anchors

An anchor places a thread on the surface:

- `snippet` — the exact text the thread is about, as the user sees it.
- `context` — only when the snippet is short or repeated: the line or
  paragraph it sits in.
- Review code adds `path`, `side` and `line`. Markdown adds `heading`, the
  nearest heading above; a markdown comment on an **image** adds `src`, the
  image's authored path, with `snippet` holding its alt text as a label. Read
  it as a comment on that image, and update `src` if you move or replace it.

## Writing the journal

Write through `journal.py`, beside this file. It stamps each event with the
time and the store's current turn:

```
python3 journal.py STORE reply   THREAD TEXT      # your words, ahead of the change
python3 journal.py STORE resolve THREAD [TEXT]    # done, with your words if given
python3 journal.py STORE block   THREAD TEXT      # blocked: what you need, and open
python3 journal.py STORE anchor  THREAD... --snippet TEXT [--context ...] [--heading ...]
                                 [--src ...] [--path ...] [--side old|new] [--line N]
python3 journal.py STORE title   THREAD TEXT      # review only
```

`STORE` is the `-comments.json` path. A `TEXT` of `-` is read from stdin;
use it for anything with quotes or several lines.

- **Write per thread, as you finish it** — never one batch at the end. Each
  write streams into the open viewer while you work.
- The journal only grows. Correct yourself with a further call (later
  events win); never edit the journal, and never write the store.
- Keep anchors current: when your own edit changes the anchored text,
  repoint the thread with `anchor` so it stays placed. Check every thread in
  the store, not only the one you are working: chained edits on one passage
  orphan every earlier thread anchored to it.
- Per thread, in this order: your reply (what you are changing and why),
  then the change and its anchor updates, then the status, the last thing you
  write for it. The user reads why with the change, and the status says it is
  done. A thread with nothing to change takes its words and status in one
  call.
- When every open thread has its disposition, the turn is over: no further
  writes to the document, the code under review, or the journal until the
  user's next send or terminal follow-up about that work.

## Status lifecycle

Shared on both surfaces: a user follow-up reopens a thread to `open` — the
follow-up IS the reopen, there is no separate action. The store-level `turn`
is the viewer's alone; never change it.

### Blocked, or done

Every thread you work ends in exactly one of two states, and you set it
(`resolve` or `block`) — the same on both surfaces:

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

When a thread's `title` is empty, set it while working the thread with
`title` and a short intent summary (a few words, e.g. "Tighten polling
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

On both surfaces the viewer waits while any thread the user sent lacks a
disposition, and comes up in front of the user when the last one lands: that
is the moment they read your work.

If you go quiet with sent threads still lacking a disposition, the host
re-pings you once with a reminder naming the store — treat it exactly like
the original send.

## Thread or terminal

Say what concerns a passage in that passage's thread. Use the terminal for
what no single passage owns, such as a question about style across the whole
document.

## Terminal corrections

When the user corrects a sent comment or edit in the terminal, including
after interrupting you, continue in its existing thread. Re-read the store
and journal, including resolved threads, and match the correction by an
explicit thread id or by its passage, file, quoted request, and conversation
context. If more than one thread fits, ask which one in the terminal before
writing or changing anything; recency alone does not identify the thread.
Feedback no single passage owns stays in the terminal.

Before continuing the work, reply on the matched thread. Capture
the relevant correction; you may rephrase or summarize it for clarity and
brevity while preserving its meaning and constraints. Say it came from the
terminal, and explain what you will change and why. For example: `Your
terminal correction is to keep the timeout and only rename the option. I’ll
preserve the behavior and update the name.` If the correction covers several
clearly identified threads, record the relevant part on each.

Follow the correction wherever it supersedes the earlier request. Preserve
the original user message: record the correction as your `reply`, never as
an invented user message or a store edit. Treat the correction as new work
even if the merged thread still says `resolved`; terminal input does not
automatically reopen it.

Then follow the usual reply → change → anchor → status order. Set the final
status only after the corrected work is visible. If the user withdrew the
request, record that and resolve once any requested cleanup is complete;
leave `open` only for a real blocker, naming what you need.

## Handing back

After working the threads, tell the user in the terminal only that you did,
briefly (a count, or one line across all threads). Your per-thread replies
already render inline on the surface; restating them makes the user read
everything twice.
