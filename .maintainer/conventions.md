# Conventions (maintainer)

Authoring conventions for this spec repo and its siblings.

## Doc resolution

- A doc a host or agent must locate resolves nearest-first up the tree from
  the content it governs, so a repo can vendor its own copy; the home-folder
  install is the fallback. Precedents: the nearest `commit-message.md`
  (code/produce-review.md), the nearest `agent-threads/` for the md runbook.

## Doc placement

- The repo root holds runtime docs only: what a consuming agent reads
  mid-loop — runbooks, and the contracts they reference. Keep them purely
  operational: no design rationale, no implementation status, no meta.
- Maintainer material lives in `.maintainer/`. README (and LICENSE) are
  maintainer-facing repo framing.

## Doc naming

The naming axis encodes how a doc enters use; who the audience is (agent vs
maintainer) is the placement axis above, orthogonal.

- ALL-CAPS is reserved for ecosystem-standard names the world already knows
  (`README`, `LICENSE`; `CODE_OF_CONDUCT` if ever needed). Our own docs never
  use caps — a caps name of ours would masquerade as a standard.
- A lowercase-kebab **verb phrase** marks a **user entry point**: a doc the
  user invokes by referencing it (`@produce-review.md`). The verb form IS the
  affordance — it advertises "you can type this".
- Everything else of ours is a **reference**: a lowercase **noun phrase**,
  the shortest that covers it (one word when one word does) — `contract.md`,
  `authoring.md`, `conventions.md`, `md/user-intent.md`. This includes docs with
  procedural content that agents are merely *pointed at* by the host or by
  another doc: a verb name there would falsely advertise @-invocability
  (`user-intent.md`, not `respond-to-user-intent.md`).
