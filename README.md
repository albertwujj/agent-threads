# agent-threads

Agent instructions and a file protocol for [plans and documents](https://github.com/albertwujj/agent-term/blob/main/docs/plan.md) and [curated code reviews](https://github.com/albertwujj/agent-term/blob/main/docs/review.md), supported by [AgentTerm](https://github.com/albertwujj/agent-term). Comment on what the agent shows you, or write directly on a document; the agent makes changes and replies in place.

## Adding it

Ask your agent:

```text
Clone the repository below into ai/agent-threads in this project, and
leave ai/ out of .gitignore.
https://github.com/albertwujj/agent-threads
```

One clone covers documents and reviews. Other locations work too ([placement](https://github.com/albertwujj/agent-term/blob/main/docs/conventions.md#placement)).

Keep it a plain clone. `git -C ai/agent-threads pull` updates it, and in a git project it shows as one untracked `ai/` line; leave it uncommitted. Stripping its `.git` stops updates, and listing `ai/` in `.gitignore` hides its docs from `@` completion.

## Using it

- **Documents.** Open a Markdown file in AgentTerm and comment or write directly on it.
- **Reviews.** Name [`code/produce-review.md`](code/produce-review.md) in a prompt; `@produce-r` completes to it. The agent prepares a curated review, which AgentTerm opens.
- **Continue in a doc.** Use [`@continue-in-doc`](conversation/continue-in-doc.md) to move a discussion out of the terminal into a document you can comment on, one per topic.

## The protocol

For implementation details and agent instructions, see [the protocol guide](docs/protocol.md).
