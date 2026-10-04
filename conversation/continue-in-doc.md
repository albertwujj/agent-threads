# Continue the conversation in a doc (agent runbook)

**Trigger:** the user references this doc (e.g. `@continue-in-doc.md`), in any
of these shapes:

- **bare** — move the topic under discussion into a doc and continue it there.
- **naming topics** — the conversation carries several; give each its own doc.
- **with fresh questions inline** — one, or several at once:
  `@continue-in-doc.md (1) why using a single loop (2) how to get user's input`
  — each question gets its own doc, seeded with the question and your current
  position.

Being asked this way means the host supports it; just create the doc(s). It
may also wait: if work is in flight, carry it to a natural stopping point
first — keeping the ongoing context intact — and create the docs then.

A terminal stream is hard to comment on, and mixing topics in it makes it
harder. A doc gives a topic its own surface: the user steers it by commenting
on the doc, so treat those comments as steering. Once a topic has a doc, its
substance lives there and the terminal only points to it; topics without one
stay in the terminal.

A conversation doc is terminal output moved into a doc, and that is all it
replaces — plan, design, and spec docs stay what they are. Write it for the
user who asked: answer their question and make it easy for them to
understand.

## Where conversation docs live

Everything sits **inside `.git`** (untracked by nature, survives reboots and
`git clean`, shared across worktrees):

```
<git-common-dir>/conversation/<topic>.md
```

- `<git-common-dir>` — `git rev-parse --git-common-dir`, absolute.
- `<topic>` — a short, self-describing, path-safe slug (non-`[A-Za-z0-9._-]`
  runs → `-`).
- Use subfolders when they help organize related topics —
  `conversation/streaming/backpressure.md`; moving and reorganizing docs later
  is fine.
- Outside a git repo, ask the user where the conversation folder should live.

The folder holds part of the conversation itself. A session resumed after a
compaction or a checkpoint that finds one of these paths reads the doc as it
would its transcript.

## Writing a topic doc

One topic per doc.

## Hand off

Print each doc's **absolute path** in the terminal, one per line — the host
makes markdown paths openable. Keep the terminal message to those lines; the
substance is in the docs.
