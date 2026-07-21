# Split a discussion into threads (agent runbook)

**Trigger:** the user references this doc (e.g. `@split.md`), in either shape:

- **bare, or naming topics** — the conversation carries several topics; split
  them out, one doc each.
- **with fresh questions inline** — one, or several at once:
  `@split.md (1) why using a single loop (2) how to get user's input` — each
  question gets its own doc, seeded with the question and your current position.

Being asked this way means the host supports it; just create the doc(s). The
split may also wait: if work is in flight, carry it to a natural stopping point
first — keeping the ongoing context intact — and create the docs then.

Mixing topics in one terminal stream makes it hard for the user to comment on
each. A document per topic gives every discussion its own surface; the user
steers a topic by commenting on its doc, so treat those comments as steering.
The terminal carries the topics that have no doc; once a topic has one, its
substance lives in the doc and the terminal only points to it.

A thread doc is split-out terminal output, and that is all it replaces — plan,
design, and spec docs stay what they are. Write it for the user who asked:
answer their question and make it easy for them to understand.

## Where thread docs live

Everything sits **inside `.git`** (untracked by nature, survives reboots and
`git clean`, shared across worktrees):

```
<git-common-dir>/discussion/<topic>.md
```

- `<git-common-dir>` — `git rev-parse --git-common-dir`, absolute.
- `<topic>` — a short, self-describing, path-safe slug (non-`[A-Za-z0-9._-]`
  runs → `-`).
- Use subfolders when they help organize related topics —
  `discussion/streaming/backpressure.md`; moving and reorganizing docs later
  is fine.
- Outside a git repo, ask the user where the discussion folder should live.

## Writing a topic doc

One topic per doc.

## Hand off

Print each doc's **absolute path** in the terminal, one per line — the host
makes markdown paths openable. Keep the terminal message to those lines; the
substance is in the docs.
