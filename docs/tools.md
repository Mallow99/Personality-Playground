# The first real tools

Tools are functions the application can actually execute. They are not capabilities
a prompt can grant by saying “you have web access.” This increment implements a
small boundary in `bfi/tools.py`, with two ways to use it:

1. **Tools & setup** in the chat opens an inspector. You explicitly select a tool
   and see its actual JSON result, including in mock mode.
2. With a real function-tool-capable local model, opt in using the composer
   checkboxes for a single message. The backend can request up to three enabled
   tool calls and then return a final reply. The checkboxes reset after the attempt.

The model's tool names and arguments are validated. Unknown tools, extra arguments,
and excessive calls fail visibly. Tools supplied in source files are not automatically
registered. No Python/shell evaluator, subprocess command, file write, exploit tool,
remote target scanner, or computer-control action is exposed.

## Project files

Set `BFI_PROJECT_ROOT=.` in `.env` to allow reads from this repository, or point it
at another project you choose. Restart the app. The tools are:

- `list_project_files`: at most 80 allowed text paths, with a bounded scan.
- `read_project_file`: relative path only; up to 12,000 characters from a UTF-8 text
  file of at most 200 KB, with truncation reported.

The policy excludes hidden components, common private/runtime directories, symbolic
links, sensitive filenames, unknown extensions, and paths outside the root. This
is a convenience boundary for a trusted local project, not a guarantee that an
arbitrary source file cannot contain a secret. Review the selected directory.
Model-assisted reads send those results to the configured model endpoint.

## Web search

Set `BFI_BRAVE_API_KEY` in the local `.env` file or environment; do not put its value
in chat or Git. Brave API access and quota are separate from any frontier subscription.
The `web_search` tool sends a query of at most 300 characters to Brave and returns
up to five titles, source URLs, and snippets. This is online access from a local app.

Snippets are not full-page reads, and the model's final wording is not an independent
verification of them. Results and tool calls are inspectable under reply provenance.
Errors produce a real failure, not invented sources. The adapter contract is tested
with simulated HTTP responses; live Brave access has not been checked without a key.

## Inspecting what happened

An assistant reply's source details include the actual tool names, arguments,
results, token counts across model calls when reported, and the number of generation
calls. JSON exports include these records and may therefore contain project text
or search queries. Only completed exchanges are committed to conversation history.
Tools may have already read files or sent a search query before a later inference
failure; a failed final reply does not undo that query. The inspector is an explicit
one-off tool call and does not add its output to chat automatically.

## Still to implement

| Capability                         | Next useful boundary                                                                             |
| ---------------------------------- | ------------------------------------------------------------------------------------------------ |
| Google Calendar / Canvas deadlines | Read-only supported API, source calendar, sync freshness                                         |
| Coding changes and tests           | User-selected working copy, visible diff, actual isolation before code execution                 |
| Sandbox                            | Verify a Windows-compatible container/VM boundary, mounts, network, resources, secrets, cleanup  |
| Computer use                       | Supported Windows interface, visible actions, stop control, user review of consequential actions |
| Proactive appearances              | Opt-in events, quiet hours, frequency limits, dismissal; separate from tool execution            |
| Frontier delegation                | Supported provider API, explicit data sharing and usage limits, model provenance                 |

A Python virtual environment separates dependencies. It is not a sandbox for
model-generated programs. A local browser preview is not a desktop-control tool.
