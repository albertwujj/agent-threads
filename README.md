# agent-threads

Two loops for working with a coding agent in writing. You comment on what it shows you, and it answers in place.

- **Plans and documents.** A markdown document opens rendered in your terminal. You write on it, as comments or as edits to the text itself, and the agent edits the source and replies where you wrote.
- **Curated reviews.** When the agent finishes a change, it writes a review of the parts that need your judgment, ordered and explained. You comment inline, on the code or on its reasoning, and it fixes and replies in the thread.

Both run on one thread store, a JSON file the host keeps for each document or review, so a host that renders one renders the other.

## Adding it

Clone this repo into `ai/` in your project, and leave `ai/` out of `.gitignore` so `@` pickers can see it. That is the default place; a clone beside the project, or under your home directory, works too ([placement](https://github.com/albertwujj/agent-term/blob/main/docs/conventions.md#placement)). One clone serves both loops. A host that supports the protocol does the rest: [agent-term](https://github.com/albertwujj/agent-term) is the reference host, and its docs show the loops in use ([plan with it](https://github.com/albertwujj/agent-term/blob/main/docs/plan.md), [the curated review](https://github.com/albertwujj/agent-term/blob/main/docs/review.md)).

## Using it

- **A review.** Name `code/produce-review.md` in a prompt; `@produce-r` completes to it. The agent produces the review and prints its link, and the host opens it.
- **A document.** Open it in the host's viewer and write on it. The host points the agent at `md/user-intent.md` with each send.
- **A conversation with several topics.** Name `discussion/split.md` (`@split`), bare or with the questions to split out. The agent gives each topic a document of its own, carried by the document loop.

## The docs

The runbooks are written for the agent. You do not need to read them to use the loops.

- [contract.md](contract.md): the thread store both surfaces share, with its files, message rules and status lifecycle.
- [code/produce-review.md](code/produce-review.md): the review loop, from trigger to reply. [code/authoring.md](code/authoring.md) is how a review is written.
- [md/user-intent.md](md/user-intent.md): the document loop, with comments and edits read as intent.
- [discussion/split.md](discussion/split.md): one document per topic.
