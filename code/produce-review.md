# Produce a review (agent runbook)

**Trigger:** the user references this doc (e.g. `@produce-review.md`) with no other
instruction → produce a review of the current change and give them a link to read and comment on.
Being asked this way means the **host supports the review protocol** — you don't need to check for
it; just produce the package.

This runbook is the **procedure** (the verbs). **How to write the review package** — its format and
how to make it good — is in **`authoring.md`**; that is the core of the job, so read it.

## Where things live

Everything for a review sits **inside `.git`**, keyed by branch (untracked by nature, per-branch,
shared across worktrees, safe from `git clean`):

```
<git-common-dir>/review/<branch>/<branch>.md             # your package — you write it (see authoring.md)
<git-common-dir>/review/<branch>/<branch>-comments.json  # the comment store (shared with the user)
```

Fill in the path above:

- `<git-common-dir>` — `git rev-parse --git-common-dir`, absolute (the *common* dir, shared across
  worktrees).
- `<branch>` — a path-safe slug of the branch: non-`[A-Za-z0-9._-]` runs → `-` (detached → short SHA);
  same slug for folder and file.

Create the folder; the store is the `-comments.json` sibling.

## Procedure

1. **Scope the change.** Anchor on a committed snapshot so references (and comment anchors) stay
   stable — a `range: A..B` with **both ends pinned** to a branch, tag, or SHA (never `HEAD` or
   `HEAD~1`); a `base: <ref>` scope is rejected. The review always opens, but if it's out of date —
   uncommitted *tracked* changes (untracked are fine), commits past the tip, or a different branch —
   it shows a red banner; the user can click **Notify agent** and you'll be prompted to bring it
   current. So **commit your work** before handing off. Make sure it's **only the user's change**;
   if the checkout carries unrelated work, scope it out first rather than reviewing someone else's
   files.
2. **Improve the commit message.** The summary and key context live there (it heads the review) —
   don't repeat them in the package. Follow the commit style in the nearest **`commit-message.md`**
   up the tree; a review snapshot needs **no** CI/CD trailers.
3. **Write the package** at that path — a markdown file that orders and explains the change. This is
   the real work; follow **`authoring.md`** for the format and craft.
4. **Hand off a launch link.** Give the user a `review://` link to your package — the scheme and the
   absolute path with nothing between them:
   ```
   review:///abs/path/to/repo/.git/review/<branch>/<branch>.md
   ```
   Clicking it renders the review (your package + the live git diff) and opens it for them. You
   don't generate or touch any `.html` — rendering is the viewer's job. When you edit the package
   the open review **re-renders in place** (no need to re-send the link).

## Round-trip: answer the user's comments

The user reads the review and leaves inline comments — on **your explanations** and on the **code**.
When they say they've commented (or click **Send to agent**, which drops a one-line pointer to the
store), address them:

1. **Read the store** (the package's `-comments.json` sibling). The schema, message
   rules (edit the JSON directly, append only), and status lifecycle are the shared
   contract in **`../contract.md`** — the same store model carries markdown-document
   threads (`../md/user-intent.md`). Review anchors extend the shared anchor:
   ```jsonc
   "anchor": { "path": "src/x.py", "snippet": "if tokens <= 0:",
               "side": "new", "line": "42",  // side/line code only; a quote on
                                             // prose/commit/preview omits them
               "context": "" }               // (path is then "(note N)" etc.)
   ```
2. **Work each non-resolved thread** per `../contract.md`:
   **before editing any code**, resolve the nearest `coding-guide.md` (this file's
   directory, then each parent up the direct chain only — closest wins,
   siblings/children never searched) if one exists, and hold any shared-checkout
   lock your workflow requires; edit code where warranted, keeping `snippet` (and
   `line`) current when your change touches an anchored line; append your reply and
   set `"status": "resolved"`. Leave a thread `"open"` only when you are genuinely
   **blocked** — you cannot do what they asked without an answer from them — and say
   exactly what you need. Doing their ask beats asking about it.
3. **Commit your code edits** — the diff is pulled from the committed range, so uncommitted
   tracked changes flag the review out of date (red banner) instead of showing your update. If the
   package's `range:` pins the tip by SHA, advance it. **Re-render** happens when you **edit the
   package** (the open review auto-refreshes), when it's re-opened (the `review://` link), or on
   refocus — it re-anchors every comment against the new diff and stamps `anchor_status`:
   - `ok` / `moved` — handled for you (code line auto-updated; a quote still on the page stays put).
   - `lost` — the anchored code/quote is gone (you rewrote or removed it). **Your worklist:**
     repoint the anchor (update its `snippet`, and `line` for code) to where the concept now lives,
     or reply and set `"status": "resolved"`.
4. **Hand back** briefly, per `../contract.md` — a count or one line; never restate the
   per-thread replies in the terminal.

## Threads born from user edits: the commit message

A thread whose first message carries an `[Edit]` block is the user marking a
change directly on the review page. The mark semantics are the shared ones in
**`../md/user-intent.md`** ("Threads born from user edits"): `<del>` is text they
struck, `<ins>` is text they added, the marks sit over the **rendered** text, and
the edit is **not applied** — it is a suggestion for you to make. A second user
message on the thread, when present, is their note about the edit.

On a review page these arrive anchored to `"(commit message)"`. Apply the intent
by **amending the commit message** (`git commit --amend` on the range tip):

- The rendered commit body reflows raw lines into paragraphs, so the marks are
  over the reflowed text — apply them to the real message and re-wrap lines
  yourself. The user's words express intent, not final wording: fix grammar,
  complete fragments, keep their meaning and voice, and keep the nearest
  `commit-message.md` style.
- Amending moves the tip SHA: update the package's `range:` if it pins the tip
  by SHA, then let the re-render re-anchor (the old quote goes `lost` — reply
  and set `"status": "resolved"` as usual).
