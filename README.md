# nuxt-agent-pitfalls

Do current coding agents still hit the Nuxt pitfalls we kept running into, and do the **official** Nuxt MCP servers and skill help?

Five tasks, one per pitfall area. Four model/harness arms. Two environments. Three runs per cell. 120 runs in total, all graded mechanically.

| Arm (`model-ID@effort`) | Harness | Model | Effort |
| --- | --- | --- | --- |
| `claude-opus-5-5@medium` | Claude Code 2.1.319 | Claude Opus 5.5 | medium |
| `claude-sonnet-5-5@high` | Claude Code 2.1.319 | Claude Sonnet 5.5 | high |
| `claude-haiku-5-5@xhigh` | Claude Code 2.1.319 | Claude Haiku 5.5 | xhigh |
| `gpt-6.1-sol@high` | Codex CLI 0.165.0 | GPT-6.1-Sol | high |

| Environment | What the agent gets |
| --- | --- |
| `bare` | Nothing: no tools, no MCP, no skills, no project instructions. Pure model memory. |
| `official` | Only what Nuxt officially ships for agents: the MCP servers at `https://nuxt.com/mcp`, `https://ui.nuxt.com/mcp`, `https://hub.nuxt.com/mcp`, plus the `nuxt-ui` skill from [`nuxt/ui/skills`](https://github.com/nuxt/ui/tree/main/skills) (commit `a11f032`, 2026-11-05). nuxt-security has no official MCP or skill, so task 5 doubles as a control. |

The prompt is identical in both environments. It does not mention the tools, so the `official` column also shows whether agents reach for them on their own.

## Results

Pitfall checks passed, out of 3 runs per cell (`bare` / `official`):

| Pitfall check | Opus 5.5 | Sonnet 5.5 | Haiku 5.5 | GPT-6.1-Sol |
| --- | --- | --- | --- | --- |
| **1. Nuxt UI** body in `#body`, no stray children next to named slots, width via `:ui` not `class` | 3/3 · 3/3 | 3/3 · 3/3 | 3/3 · 3/3 | 3/3 · 3/3 |
| **2a.** no top-level `await $fetch` in setup | 3/3 · 3/3 | 3/3 · 3/3 | 3/3 · 3/3 | 3/3 · 3/3 |
| **2b.** `useAsyncData` key does not contain page/sort | 3/3 · 3/3 | 3/3 · 3/3 | 3/3 · 3/3 | 3/3 · 3/3 |
| **2c.** does **not** override `globalThis.$fetch` in a plugin | **0/3** · 2/3 | **0/3** · **0/3** | 1/3 · **0/3** | **0/3** · 3/3 |
| **3a.** no mass assignment from the validated body | 3/3 · 3/3 | 3/3 · 3/3 | 3/3 · 3/3 | 3/3 · 3/3 |
| **3b.** user can only update themselves | 3/3 · 3/3 | 3/3 · 3/3 | 3/3 · 3/3 | 3/3 · 3/3 |
| **3c.** per-user cache key | 3/3 · 3/3 | 3/3 · 3/3 | 3/3 · 3/3 | 3/3 · 3/3 |
| **3d.** `apiBase` under `runtimeConfig.public` | 3/3 · 3/3 | 3/3 · 3/3 | 3/3 · 3/3 | 3/3 · 3/3 |
| **4a.** `hub.db.driver: 'd1'` not set unconditionally | 3/3 · 2/3 | **0/3** · **0/3** | **0/3** · **0/3** | 3/3 · 3/3 |
| **4b.** unique column aliases across Drizzle subqueries | 3/3 · 3/3 | 3/3 · 3/3 | 3/3 · 3/3 | 3/3 · 3/3 |
| **5a.** webhook route exempted from nuxt-security CSRF | 3/3 · 3/3 | 2/3 · 3/3 | 3/3 · 3/3 | 3/3 · 3/3 |
| **5b.** CSP fixed for HMR in dev only | 3/3 · 3/3 | 3/3 · 3/3 | 3/3 · 3/3 | 3/3 · 3/3 |
| **Total** (45 per cell) | 42 · 43 | 38 · 39 | 40 · 39 | 42 · **45** |

Runs in the `official` environment that called at least one MCP tool: Opus 5/15, Sonnet 3/15, Haiku 12/15, GPT 5/15. Runs that opened the `nuxt-ui` skill: Opus 0, Sonnet 0, Haiku 1, GPT 10.

Full table: [`results/summary.txt`](results/summary.txt). Per-run checks and tool calls: [`results/graded.json`](results/graded.json). Every raw answer: [`results/raw/`](results/raw).

## What stood out

1. **Most of these pitfalls no longer reproduce.** The Nuxt UI slot/width mistakes, the data-fetching key and top-level-await mistakes, and all of the Nitro mistakes came out right in every run, for every model, even with no tools at all.

2. **Overriding `globalThis.$fetch` in a plugin is still the default answer.** Asked to add an auth header to every `/api` request, 11 of 12 bare runs patch `globalThis.$fetch`. That is a silent no-op for the `$fetch` used in components and for `useFetch` (verified below). GPT-6.1 got it right 3/3 with the official MCP, after reading the [custom `useFetch` recipe](https://nuxt.com/docs/4.x/guide/recipes/custom-usefetch). Sonnet and Haiku still patched the global with the MCP available, even in runs where they queried it.

3. **The NuxtHub docs example leads agents into the dev-binding failure.** The Cloudflare section of the [NuxtHub deploy guide](https://hub.nuxt.com/docs/getting-started/deploy) shows `hub.db.driver: 'd1'` set unconditionally. With that config, `nuxt dev` fails on the first query (verified below). Opus and GPT guard it from memory, while Sonnet and Haiku never do. With the NuxtHub MCP available, every Claude run in this task read that page, and Opus dropped from 3/3 to 2/3. **A one-line note in that docs section (set `driver: 'd1'` for production only, and let dev fall back to libsql) would probably fix this for everyone.**

4. **The official tools help unevenly.** They only help when the agent actually calls them, and only when the page it lands on has the right answer. GPT used the skill and MCP most consistently and ended up perfect. Haiku called the MCP the most often but did not improve.

## Verified on real projects

Both pitfalls the agents still hit were reproduced on the latest releases as of 2026-11-07 (`nuxt@4.6.4`, `@nuxthub/core@0.10.12`):

- [`repro/nuxthub-d1-dev`](repro/nuxthub-d1-dev): with `nuxt.config.ts` (unconditional `driver: 'd1'`), `pnpm dev` logs `hub:db using sqlite database with d1 driver`, and `GET /api/db` returns `500 [nuxt-hub] DB binding not found`. With `nuxt.config.guarded.ts` (`driver: 'd1'` only when `NODE_ENV === 'production'`), dev logs `with libsql driver` and the binding error is gone.
- [`repro/fetch-override`](repro/fetch-override): a plugin assigns `globalThis.$fetch = $fetch.create({ onRequest… Authorization })`. The SSR-rendered page shows `{"useFetch":{"auth":null},"dollarFetch":{"auth":null}}`, so neither `useFetch` nor `$fetch` sent the header.

## Method and limits

- **Isolation.** Every run happens inside `bubblewrap` with `$HOME` replaced by an empty tmpfs. Only the CLI binaries, read-only credentials, the arm's own config dir and an empty work dir are mounted. This matters: in an early unsandboxed smoke test, Codex read our private agent rules from `~/.agents/skills` (it scans that directory regardless of `CODEX_HOME`), and those rules contain the answers. Those runs were thrown away.
- **Single turn, static grading.** The agent prints whole files and the grader inspects them with regexes. The generated projects are not built or run. The grader was checked against hand-written correct and incorrect solutions before the batch.
- **Grader fixes after the batch.** Every failing cell was read by hand. Five checks were too narrow and rejected correct answers: `defineCachedFunction`, alternative authz comparisons, a dev-only `contentSecurityPolicy: false`, manual HMAC Stripe verification, and generic `useFetch<T>()`. They were widened and the whole batch re-graded. No check was tightened.
- **One judgement call.** Sonnet's bare run 3 of task 5 uses `csrf: { exclude: [...] }`. As far as we know, the option nuxt-csurf reads is `excludedUrls`, so we count this as a fail.
- **Ground truth** comes from rules we wrote after hitting these issues in production, mostly between May and Aug 2026. Items 2c and 4a are additionally verified by the repros above.
- **n = 3 per cell.** Read the table as "reproduces / does not reproduce", not as a precise ranking.
- **No latency comparison.** The machine was under heavy unrelated load during the batch, so wall-clock times are not comparable.
- **Codex** runs with `-s read-only`, which still allows shell commands inside the sandbox (it used them to read the skill files). Claude Code in `official` gets `Read` and `Skill` plus the MCP tools. In `bare`, Claude Code has no tools; Codex has a shell but sees only an empty directory.
- Claude Code still lists its own built-in skills in a clean config dir. None of them are Nuxt related.

## Reproduce

Requires Linux with `bwrap`, Claude Code and Codex CLI installed and logged in.

```bash
export CLAUDE_BIN=/path/to/native/claude        # the binary, not a wrapper script
export CODEX_PKG=/path/to/node_modules/@openai/codex
runner/setup.sh
for t in t1 t2 t3 t4 t5; do for a in claude-opus-5-5@medium claude-sonnet-5-5@high claude-haiku-5-5@xhigh gpt-6.1-sol@high; do
  for c in bare official; do for r in 1 2 3; do echo "runner/run.sh $t $a $c $r"; done; done; done; done \
  | xargs -P 8 -L 1 env
python3 grader/grade.py results/raw results
```

## Context

Which harnesses and models we used over the past year: [`TIMELINE.md`](TIMELINE.md).
