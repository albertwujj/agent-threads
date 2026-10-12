# Troubleshooting

## A helper will not run

When `journal.py` or `open-threads.py` cannot run (no `python3`, or a sandbox
that refuses to execute it), stop. Show the user the command and its error,
say what would fix it, and wait:

- No `python3`: install it. On macOS, `xcode-select --install` provides it.
- A sandbox blocks the file: allow it, or clone agent-threads into the
  project.

Write the files by hand only when the user asks you to; `format.md` is the
line format.

## A helper rejects a call

An exit with a message naming a wrong thread id, store path, or argument is
your call to fix: re-read the threads with the tool and call again.
