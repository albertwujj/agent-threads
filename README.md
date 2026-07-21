# agent-threads — human↔agent review threads

This repo is the **agent-facing spec** for a threaded human↔agent conversation
anchored to content and persisted as a `-comments.json` store. One shared model
carries two surfaces:

- a **code-diff review** — an agent writes a markdown *review package* that
  references and explains a change; the human reads it against the live
  `git diff` and comments, and the comments flow back to the agent.
- a **live markdown document** — the human comments on and edits a document the
  host renders; those comments and edits (intent, not final wording) reach the
  agent the same way.

It's intended for a **terminal host that supports the protocol**: the host
renders each surface and carries the conversation back to the agent. The renderer
and viewer live in that host; this repo is just the spec. **Nothing to install here.**

[agent-term](https://github.com/albertwujj/agent-term) is the reference host — it
renders both surfaces and carries inline comments back to the agent
([see it in action](https://github.com/albertwujj/agent-term#it-reviews-its-own-work-you-review-what-matters)).

## Docs

- **[contract.md](contract.md)** — the shared thread-store contract (schema, message rules, status lifecycle) both surfaces build on. **Read this first.**
- **code/** — the code-diff review surface:
  - **[code/produce-review.md](code/produce-review.md)** — the agent runbook for the review loop (trigger → write the package → review → respond to comments). The user invokes it with `@produce-review.md`.
  - **[code/authoring.md](code/authoring.md)** — how to write a review package (the format + the craft).
- **md/** — the live-markdown surface:
  - **[md/user-intent.md](md/user-intent.md)** — the agent runbook for threads on a live markdown document (comments + user edits as intent).
- **discussion/** — splitting a multi-topic conversation onto the live-markdown surface:
  - **[discussion/split.md](discussion/split.md)** — the agent runbook: one document per topic, each carried by the markdown thread loop. The user invokes it with `@split.md`, bare or with the questions to split out.
