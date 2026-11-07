# Which harness and model we used, and when

Reconstructed from commit co-author trailers in our oldest active Nuxt project (started Nov 2025),
the history of our shared agent-config repo (started late Apr 2026), and our dispatch logs (from Aug 2026).
Months are when a tool first shows up in the record, not exact adoption dates. Many commits carry
no trailer at all, so read this as "what was in use", not as usage share.

| Period | Main session | Side / background work |
| --- | --- | --- |
| Nov 2025 | project starts with `CLAUDE.md`, `AGENTS.md` and Copilot instructions checked in | Gemini Code Assist reviews PRs |
| Dec 2025 | **Claude Code**: Sonnet 4.5, Opus 4.5 | |
| Jan – Mar 2026 | Claude Code: Opus 4.5 → Opus 4.6 (1M) | |
| Apr 2026 | Claude Code | short GitHub Copilot trial; Codex CLI config added |
| May – Jul 2026 | Claude Code: Opus 4.7 → Opus 4.8 → Opus 5 | Codex (GPT-5.5 → 5.6) for offloaded tasks, including commit review for a while |
| Aug – mid Oct 2026 | Claude Code: Opus 5 → **Opus 5.5** (late Sep) | multi-vendor: background tasks routed through the Pi coding agent to GPT-5.6/6, Gemini Flash and Grok; Cursor and Devin as extra carriers. Sonnet 5.5 took over implementation work from Sep 30 |
| mid Oct 2026 – now | **Claude Code only**: Opus 5.5 (planning, root-cause, UI, every commit review) + Sonnet 5.5 high (scoped implementation) + Haiku 5.5 (code lookup) | parallel sessions in Herdr panes and Claude Code cloud sessions; GPT, Gemini, Grok, Cursor and Devin all retired one by one between Sep 30 and Oct 22 |

Recent split on our main dev machine (first week of Nov 2026, by output tokens): ~64 % Opus 5.5, ~36 % Sonnet 5.5.

The pitfalls in this repo were mostly written down as rules between May and Aug 2026, i.e. while
the main model was Opus 4.7/4.8 → Opus 5 and part of the backend work went to GPT-5.x via Codex.
The experiment in this repo checks whether today's models still hit them without those rules.
