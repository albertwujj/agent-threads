# Markdown document threads (agent guide)

**Trigger:** a terminal message names a markdown document, its `-comments.json`
store, and an open-thread count. Unlike a review — which you start yourself, so
you know where everything lives — this loop starts host-side (the user opened
the document in their viewer), so that message is your introduction to the
document: read both paths from it rather than assuming any prior context. The
user is reading — and editing — the document live while you work; their
comments and edits arrive as threads. Being pointed this way means the host
supports the protocol; just work the threads.

The thread store, message rules, and status lifecycle are the shared
contract in **`../contract.md`** — read it first. This runbook is what's specific
to the markdown surface.

## Where things live

For a document at `/path/NAME.md`, the store sits in a folder beside it:

```
/path/.agent-threads/NAME-comments.json
```

`NAME` is the document's basename verbatim (no case or character transformation);
the markdown extension is replaced by `-comments.json`, matching the review
store's derivation. `/docs/launch-plan.md` →
`/docs/.agent-threads/launch-plan-comments.json`.

The folder keeps the store next to its document without putting an untracked
file beside every document that has one, so a single `.agent-threads/` line in a
global gitignore covers the surface everywhere. Read the path from the trigger
message rather than deriving it.

The viewer creates it; a missing store means no threads yet — never create it
yourself.

## Anchors on this surface

Markdown anchors are prose anchors: `snippet` (exact text in the document),
optional `context`, and `heading` (the nearest heading above) — no
`path`/`side`/`line`, and no `anchor_status` to act on here. The viewer places
each thread by finding its `snippet` in the live document, and shows one whose
text is gone as an orphan; it never asks you to repoint an anchor, because you
re-read the document from disk each pass (below) and work from the live text,
not a stored position. Keep `snippet` current when your own edits change the
anchored text so the thread stays placed; if that would leave it trivially short
or common (a single stopword), widen it to the surrounding phrase.

A comment on an **image** is the exception: an image carries no text, so its
anchor uses `src` (the image's path as authored in the document) with `snippet`
holding the image's alt text as a label. Read it as a comment on that image; if
your edit replaces or moves the image, update `src` to keep the thread placed.

## Threads born from user edits

A thread whose first message carries an `[Edit]` block is the user marking a
change on the document. The marks are the passage as the user sees it
(rendered, without markdown syntax) with their suggestions in place: `<del>` is
text they struck to remove, `<ins>` is text they added — `The polling
<del>utilizes</del><ins>uses</ins> a timer`. A pure deletion carries only
`<del>`, a pure insertion only `<ins>`. Every edit arrives this way, markup
blocks included — the marks always sit over the rendered text, never the
markdown source.

A mark can carry real newlines. In a **fenced code block** —
`<ins>const x = 1;\nconsole.log(x);</ins>` — the break is part of the
suggestion: reproduce it exactly. In **prose**, a newline inside `<ins>` is
the user starting a new line on the rendered surface, where block structure
is invisible: the break's position is theirs, its markdown form is yours.
Choose the form from the content and its surroundings — a short title-shaped
line before related prose may become a heading, an enumeration becomes list
items, otherwise a new paragraph or a continuation of the block. Keep the
user's words verbatim and never fold their lines back together.

**The edit is not applied — it is a suggestion for you to make.** Re-read the
document from disk and apply the marks to the source: struck text is removed,
inserted text is added, and you decide how it lands in the markdown (which
syntax to keep or drop, since the marks are over rendered text). A second user
message on the same thread, when present, is the user's note about the edit —
read the two together.

**The user's words express intent, not final wording.** Re-read the document
from disk, then apply the intent: fix grammar and spelling, complete
fragments, and adjust surrounding text for consistency. Keep the user's
meaning and voice. Reply describing what you did and set
`"status": "resolved"`.

## Round trip

Per open thread: interpret and edit the document where warranted → keep
anchors current → append your reply → set `"status": "resolved"`. The order
is a rule, not optional: the document write lands first, so `resolved` never
claims a change the user cannot see yet (`../contract.md`,
resolve-after-visibility). Append only; hand back one brief terminal line,
not a restatement (both rules in `../contract.md`).

Leave a thread `"open"` only when you are genuinely **blocked** — you cannot
do what they asked without a decision or an answer from them — and say
exactly what you need in your reply. Everything you resolved folds into a
single line under its block, so an open thread is the one thing the user must
look at. Blocking on an **edit** also keeps its block locked: while the thread
is open the user cannot revise that suggestion in place, only answer you. So
resolve an edit whenever you reasonably can. Do their ask when you can; ask
only when you must.
