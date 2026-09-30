# Protocol and agent guides

AgentTerm displays documents and reviews, records your feedback, and points the agent at the appropriate guide. The guides in this repo tell the agent how to prepare a review and respond to comments and edits.

Documents and reviews share a thread format. Each has a JSON store written by the host and an append-only JSONL journal written by the agent. The host combines them to display replies and status. The document and review guides describe their respective content and anchors.

For another host, or for changes to this repo:

- [Shared contract](../contract.md): files, messages, and thread status.
- [Document feedback](../md/user-intent.md): comments and edits read as intent, followed by document updates and replies.
- [Producing a review](../code/produce-review.md): preparing the package, opening it, and responding to feedback.
- [Review authoring](../code/authoring.md): selecting and explaining what matters, and the package format.
- [Splitting a discussion](../discussion/split.md): one document per topic.

For setup and everyday use, return to the [README](../README.md).
