# The thread store (shared contract)

One thread model carries the human↔agent conversation on two surfaces: a
**review package** (see `code/produce-review.md`) and a **live markdown
document** (see `md/user-intent.md`). The store is a `-comments.json` file; where
it lives is surface-specific and defined in each runbook. This doc is the
shared contract: the schema, the message rules, and the status lifecycle.

## Schema

```jsonc
{ "version": 1,
  "turn": 4,                     // logical clock: count of user send-batches;
                                 // the viewer ticks it, you never write it
  "threads": [
  { "id": "t…",
    "title": "",                 // short intent summary; you set it (see Titles)
    "anchor": {
      "snippet": "if tokens <= 0:",  // the real anchor: exact text on the surface
      "context": ""                  // only when snippet is short/repeated: the
    },                               // enclosing line or paragraph it sits in
    "anchor_status": "ok",       // ok | moved | lost — review stamps it;
                                 // markdown doesn't (it anchors by snippet live)
    "status": "open",            // open (blocked on the user) | resolved (done)
    "messages": [ { "author": "user", "body": "…", "ts": 1719500000000, "turn": 4 } ]
  } ] }
```

Surfaces extend the anchor: review code anchors add `path`/`side`/`line`;
markdown anchors add `heading`, and a markdown comment on an **image** adds
`src` (the image's authored path) with `snippet` holding the image's alt text
as a label — read it as a comment on that image, and update `src` if you move
or replace it. `title` and the `turn` fields are optional and absent in older
stores.

## Message rules

- The store is the source of truth. You edit the JSON directly.
- **Append only**: add `{ "author": "agent", "body": "…", "ts": <ms>, "turn": <store turn> }`
  messages (stamp the store's current `turn`); never edit or delete the
  user's messages. `ts` is real epoch milliseconds — `date +%s%3N` — never an
  invented or rounded number.
- Keep anchors current: when your edit changes the anchored text, update the
  thread's `snippet` (and surface-specific fields) so it stays placed.

## Status lifecycle

Shared on both surfaces: a user follow-up reopens a thread to `open` — the
follow-up IS the reopen, there is no separate action. The store-level `turn`
is the viewer's alone; it increments on each user send-batch, so read it (and
stamp it on your messages) but never change it.

### Blocked, or done

Every thread you work ends in exactly one of two states, and you set it — the
same on both surfaces:

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

When a thread's `title` is empty, set it while working the thread: a short intent
summary (a few words, e.g. "Tighten polling wording"). Threads born from user
edits especially need one — their first message is a diff, which makes a poor
label. The review viewer shows the title on the collapsed thread line.

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

## Handing back

After working the threads, tell the user in the terminal only that you did,
briefly (a count, or one line across all threads). Your per-thread replies
already render inline on the surface; restating them makes the user read
everything twice.
