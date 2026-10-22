---
name: scripts-untracked-in-git
description: "Scripts waren bis 2026-10-22 ungetrackt; seitdem committet und auf GitHub (Otigo04/DUSK_BELL). Vorsicht bei git-Redirects auf Projektdateien"
metadata:
  node_type: memory
  type: project
  originSessionId: 85cc25d5-ad80-4490-a687-5418c5c2bc94
  modified: 2026-10-20T19:03:45.628Z
---

UPDATE 2026-10-22: alles committet und nach https://github.com/Otigo04/DUSK_BELL.git (main) gepusht; git ist jetzt ein echtes Backup. Historischer Stand unten.

As of 2026-10-20 the repo had only one commit ("initial Unity project commit"); folders like Assets/_Project/Scripts/NPC, Dialogue, UI, Interaction, DayNight and most Editor builders are untracked (`??`).

**Why:** `git show HEAD:<file>` / `git checkout` cannot restore these; a shell redirect like `git show ... > file` truncated NpcMover.cs once before failing.
**How to apply:** Before rewriting such a file, copy it to the scratchpad first. Never redirect git output onto a project file. Suggest the user commit. Originals from 2026-10-20 rewrites are in `_Backup_vor_Claude_2026-10-20/` at the project root.

Also: the user sometimes runs a second Claude session in the same project/Unity editor in parallel — check ListAgents and coordinate (see [[parallel-sessions]]).
