# Capture ideas, then decide what to build

The optional **Best Friend Initiative — project home** in Notion is the live idea
inbox and project board. Its link is in the project conversation. In this workspace,
private connection IDs are kept in ignored `data/project-links.json`; they are not
required to run BFI or included in the repository. No automatic Notion sync runs.

Say an idea naturally in a chat that can access the board. The assistant should
preserve the useful detail, look for a related card, capture it without requiring a
due date, and distinguish a new possibility from a chosen implementation. The owner
also expects actual implementation in Git: the board is not a substitute for code.

| Column   | Meaning                                                                 |
| -------- | ----------------------------------------------------------------------- |
| Inbox    | Capture first, sort later; rough and unfinished is fine                 |
| Next     | A deliberately small shortlist, normally no more than three             |
| Building | Work currently being implemented                                        |
| Waiting  | A named dependency such as hardware, credentials, or a decision         |
| Later    | Preserved without pressure or an implicit commitment                    |
| Done     | The specific deliverable has evidence; broader requests can remain open |

Cards have Name, Status, Area, Kind, a small Next step, and an ID. Only the title is
needed for capture. The three-card Next convention is not an automated limit.
There are no fabricated deadlines or owners. School deadlines come from Google
Calendar with Canvas synced into it, not from this project board.

The initial capture covers the local PC requirement, loaders/Strata, one to three
specialist characters, model assignment and training, all three visual palettes,
loading transitions, pose assembly, corner presence, proactive appearances, tools,
sandboxing, licensed reuse, memory, and frontier assistance. These requests are
preserved in `characters.md`, `integrations.md`, `tools.md`, `vision.md`, and the
board. Private personal captures should stay out of the public repository.

When returning to the project, start with Next, not the entire backlog. Learn the
existing implementation using `learning.md` when the PC arrives; no immediate study
session is required to keep capturing ideas now.
