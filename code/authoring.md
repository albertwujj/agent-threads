# Authoring a review package

A **review package** is a single markdown file you (the agent) write to make a
change easy to review. A user runs a tool that **combines your file with the git
diff** into one review, then reads it and **comments — on your explanations and on
the code.**

The diff already exists in git. **Your value is to surface what matters** — order,
group, and explain the parts that need a human's judgment, and leave out the parts
that don't. Aim to cost the reviewer the **least time** while leaving them confident
they understood the change. Since they comment on your **reasoning** as much as the
code, make your explanations clear and defensible. (The full review loop — how
comments come back and how you respond — is in `produce-review.md`.)

## Highlights, not completeness
A review is **not** a complete tour of the diff — it's the highlights. Show what helps
the reviewer understand the change and what needs their judgment; leave the rest out so
the important parts stand out — **don't aim for completeness.**

- **Skip the trivial.** Pure import add/remove, renames, formatting, boilerplate,
  generated files, mechanical refactors — don't embed or explain them. They cost the
  reviewer time and bury the signal.
- **Don't list moved/re-indented lines.** When a block only moves or re-indents (e.g.
  wrapping a body in a `with`/`try`), a line diff shows the whole block as remove+add
  even though nothing changed. Narrow the `:::diff` `L<start>-<end>` to the
  genuinely-new lines only, and say in one line that the rest is unchanged (moved).
- **Lead with what needs judgment.** New behavior, non-obvious logic, anything risky or
  subtle — that *is* the review.
- **Surface trade-offs and seek confirmation — especially ones you haven't already
  discussed with the user.** If you chose between approaches, made an assumption, or
  accepted a downside, call it out and ask. A silent trade-off is the most expensive
  thing for the reviewer to discover later.

## The summary lives in the commit message — don't repeat it here
**Improve the commit message** — clear subject; body with the summary and any key
context, per the nearest `commit-message.md` up the tree. The package itself is
**only** the organized, explained diff.

## File format
Markdown with a small YAML frontmatter:

```markdown
---
range: origin/main..add-rate-limiter   # branch (or SHA) tip — pinned, not HEAD
---

## <section heading>
<your explanation — the *why*, and how this section relates to the others>

:::diff src/limiter.py L40-60
:::diff src/server.py L88-95
```

- **Frontmatter** — just the scope: a committed `range: A..B`. A `base: <ref>`
  scope (base → working tree) is **rejected** — it reviews the volatile working
  tree, where comment anchors drift. **Pin both ends** to stable refs — a branch
  (`origin/main`, your feature branch), a tag, or a SHA — and **never `HEAD` or a
  HEAD-relative ref** like `HEAD~1`: a moving base silently re-scopes as commits
  land, and a moving tip re-resolves on a branch switch, so a switched-away review
  still looks in sync. The review **always opens**; if it's out of date it shows a
  red banner — for uncommitted *tracked* changes (untracked are fine and expected),
  commits past the tip, or HEAD on a different branch — with a **Notify agent**
  button. If the user clicks it you're prompted to bring the review current; the
  open review then auto-refreshes and the banner clears. (Title comes from the
  commit; don't set one.)
- **Headings** (`##`, `###`, …) — your sections and their nesting. The order of
  sections **is** the reading order (see *Ordering*).
- **Prose** — your explanation, plain markdown.
- **`:::diff <path>`** — embed that file's whole diff. **`:::diff <path>
  L<start>-<end>`** — embed only the new-side line range (a block/hunk). The diff
  is pulled live from git; you only reference it.
- **`:::code <path> L<start>-<end>`** — embed that slice of the file as it stands
  at the range tip, with no diff. Use it for code the change depends on or copies:
  a callee the new code calls, the existing shape a new block follows. Slice it as
  tight as a diff block; a range is required. The paragraph right before the
  directive renders beside the code, so put the why there. If the slice touches
  changed lines the viewer marks them; show changed code with `:::diff`.
- **Range form is exact**: `L<start>-<end>`, both ends, dash between. A single
  line is `L42-42`.

A directive that fails to parse (`L42`, `L42:50`, `42-50`), a `:::code` with no
range or past the end of the file, or a `:::diff` range with no changes renders
as a problem card where the block would be, and the review shows an amber
**directive errors** banner listing them with a **Notify agent** button. Clicking
it prompts you with the path of `<package-stem>-errors.json`, the same list; fix
the package and the open review re-renders. Changed lines you leave out are never
flagged.

## Mark what needs a decision — `CONFIRM:`
The viewer builds its outline from your headings, so that outline is the only place
a reviewer sees **where they must act** before opening anything. Put the ask in the
heading text, not just in the prose underneath:

- Prefix a section whose content needs a decision with **`CONFIRM:`** —
  `## CONFIRM: per-attempt charge at high retry counts`.
- **Leave every other heading unmarked**, and say once near the top that unmarked
  sections need no response. Absence of the marker is the signal; don't add a
  second marker for "FYI".
- **All caps on purpose.** It is a label, not prose — the same family as `TODO` /
  `NOTE` — so it stays legible among ordinary headings and stays greppable
  (`rg '^#+ CONFIRM:'` enumerates every open ask).
- **One decision per `CONFIRM:` section.** If a section grew three asks, it is
  three sections — otherwise a reviewer answers one and the others die quietly.
- State the ask itself in the section: what you chose, what it costs, and what
  you'd do instead. "Is this OK?" gives the reviewer nothing to push against.

## Ordering and grouping — your main levers
A diff arrives in a fixed, mechanical shape: file by file, top to bottom.
**Don't blindly follow it** — re-grouping and re-ordering the blocks into a
conceptual narrative is the point, and you have minimal restriction:

- **Group by concept, not by file.** Related blocks from *different* files belong
  under one heading if they're understood together (e.g. a new function and its
  call site). Put several `:::diff` from several files in one section.
- **Order so the reader holds less in their head.** Put a change *before* the
  changes that depend on it — foundational first, dependents after.
- **Explain the order — the dependency narrative.** Because *you* control order,
  use it to tell the story, and name the relationships in one line:
  - *why-before*: "**used by** the *Wiring* change below."
  - *why-after*: "**builds on** the limiter from *Core* above."
  Order + these one-liners let a reviewer follow the change forward and backward.

## What to explain — and what not to
- **Do** explain the **why**, and **how blocks relate** (enables / builds-on /
  guards / replaces). Those relationships aren't visible in any single spot — they
  are exactly what you add.
- **Do not** restate **what** the code does.
- **Show, don't describe, the unchanged code a block leans on.** A callee the new
  code calls, or the shape it copies, is a `:::code` slice under your one-line why,
  not a paragraph restating it.
- **Do not** repeat **code comments.** Code comments describe the code; if it's
  already in a comment, the reviewer will read it in the diff. Your prose is for
  the reasoning and cross-block story that *isn't* in the code.
- **Explain the *change* in the package; explain the *code* in the code.** This
  split is the point of the package:
  - **Change-talk belongs here — and must never become a code comment.** A diff
    needs delta explanation: what this replaces, why this approach over the old
    one, what actually changed vs. what merely moved. Code comments can't hold
    it — a comment narrating the change ("now uses X", "was Y before") describes
    history, not the code, and is stale noise the moment it merges. The package
    is the home change-talk never had; that is what makes a diff reviewable.
  - **Code-talk belongs in the code, as part of the change.** When a block needs
    prose about what it does or why it's written that way, write it as a code
    comment — durable, serving every future reader, and read right in the diff.
    Often the better fix is clearer code — a better name, a constraint stated
    where it holds — and then nothing needs saying.
- **Prefer small, focused blocks** — slice the diff into the smallest coherent
  bites (`L<start>-<end>`) and put attention where it matters.

## Worked example
```markdown
---
range: origin/main..add-rate-limiter
---

## The limiter, and where it guards
The bucket admits a request only when it holds ≥ 1 token. Introduced first; **used
by** the server wiring below.

:::diff src/limiter.py

The check slots into `handle()` between parse and auth; the existing order below
(unchanged) is why it can sit there without touching auth.

:::code src/server.py L70-84
:::diff src/server.py L88-95

The server check sits *before* auth (it **builds on** the limiter above) so
unauthenticated floods are shed early.

## CONFIRM: default refill rate
**Builds on** the limiter: exposes its capacity and refill rate as settings.

:::diff src/config.py L20-28

I defaulted the refill to 10/s, which sheds traffic on the current p99 burst. The
alternative is 25/s — never sheds, but a real flood reaches auth. Say which you
want; 10/s is the safer default and the one I'd keep.

## Tests
:::diff tests/test_limiter.py
```

## Quality bar — self-check before handing it over
- [ ] Commit message improved — summary + key context live **there**.
- [ ] **Highlights only** — trivial/mechanical changes (imports, renames, formatting) left out.
- [ ] **Trade-offs and undiscussed decisions called out** — each its own **`CONFIRM:`** section, stating the choice, its cost, and the alternative.
- [ ] A line near the top says unmarked sections need **no response**.
- [ ] Sections grouped **by concept**; related cross-file blocks together.
- [ ] Order goes **foundational → dependent**; each section says **how it relates**.
- [ ] Prose adds **why/relationships** — no restated code, no repeated code comments.
- [ ] Change-talk (the delta's what/why) lives in the **package** — never as a code comment narrating the change.
- [ ] Code that needed explaining got a **code comment** (part of the change), not review prose.
- [ ] Non-obvious blocks called out at **line granularity**; routine ones whole-file.
- [ ] Unchanged code the reader needs to judge the change (a callee, a shape copied) shown with **`:::code`**, sliced tight, the why in the paragraph before it.
