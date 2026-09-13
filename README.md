# agent-threads

A piece of [agent-term](https://github.com/albertwujj/agent-term): the loop for writing on [plans and documents](https://github.com/albertwujj/agent-term/blob/main/docs/plan.md), and the loop for the [curated review](https://github.com/albertwujj/agent-term/blob/main/docs/review.md). You comment on what the agent shows you, and it answers in place.

## Adding it

Ask your agent:

```text
Clone https://github.com/albertwujj/agent-threads into ai/ in this project,
and leave ai/ out of .gitignore.
```

One clone serves both loops. A clone beside the project, or under your home directory, works too ([placement](https://github.com/albertwujj/agent-term/blob/main/docs/conventions.md#placement)).

## Using it

- **A review.** Name `code/produce-review.md` in a prompt; `@produce-r` completes to it. The agent produces the review and prints its link, and the terminal opens it.
- **A document.** Open it in the viewer and write on it. The terminal points the agent at `md/user-intent.md` with each send.
- **A conversation with several topics.** Name `discussion/split.md` (`@split`), bare or with the questions to split out. The agent gives each topic a document of its own, carried by the document loop.

## The protocol

For another host, or for working on this repo. Both loops run on one thread store, a JSON file the host keeps for each document or review, so a host that renders one renders the other. The runbooks are written for the agent; you do not need to read them to use the loops.

- [contract.md](contract.md): the thread store both surfaces share, with its files, message rules and status lifecycle.
- [code/produce-review.md](code/produce-review.md): the review loop, from trigger to reply. [code/authoring.md](code/authoring.md) is how a review is written.
- [md/user-intent.md](md/user-intent.md): the document loop, with comments and edits read as intent.
- [discussion/split.md](discussion/split.md): one document per topic.
