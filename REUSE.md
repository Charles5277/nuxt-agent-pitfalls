# Re-running this on another model (for example a cheaper one)

The runner takes any model and effort on the command line. You do not edit a case table. The arm id is built as `<model-id>@<effort>` and is the name used in result files and in the grader output, so your arm shows up next to ours.

## Prerequisites

- Linux with `bwrap` (bubblewrap). Every run happens inside it, with `$HOME` replaced by an empty tmpfs, so the agent cannot read your local rules, skills or repos.
- Claude Code (we used 2.1.319) and/or Codex CLI (we used 0.165.0), both logged in. Credentials are mounted **read-only** into the sandbox (`CLAUDE_CREDENTIALS`, `CODEX_AUTH`, defaults `~/.claude/.credentials.json` and `~/.codex/auth.json`).
- `CLAUDE_BIN`: the native Claude Code binary, not a wrapper script. `CODEX_PKG`: the `@openai/codex` npm package directory that contains `vendor/*/bin/codex`.
- `python3`, `git`, network access (the sandbox fetches the `nuxt/ui` skill once and the agents reach `nuxt.com`, `ui.nuxt.com`, `hub.nuxt.com` in the `official` environment).

```bash
export CLAUDE_BIN=/path/to/native/claude
export CODEX_PKG=/path/to/node_modules/@openai/codex
runner/setup.sh        # builds ./.sandbox once: bare and official config dirs
```

## Fastest run: one task, one run

```bash
runner/run.sh t2 claude claude-haiku-5-5 low bare 1
python3 grader/grade.py results/raw results     # grades everything in results/raw (writes results/graded.json and prints the table)
```

Arguments: `<task t1..t5> <cli claude|codex> <model-id> <effort> <env bare|official> <run#>`. The result is `results/raw/t2__claude-haiku-5-5@low__bare__1.txt` (the answer) plus `.tools` (tool-call counts). An existing non-empty `.txt` is never overwritten, so a partial batch can be resumed by running the same command again. `DRY_RUN=1` prints the resolved arm and file name without running anything. The original short form `runner/run.sh t1 claude-opus-5-5@medium bare 1` still works.

To keep your trial out of the committed tables, point the grader elsewhere: copy the files you want graded to a scratch directory and run `python3 grader/grade.py <dir> <out-dir>`. `results/examples/` holds one such smoke run.

## Full set: 5 tasks × bare/official × n runs

```bash
M=claude-haiku-5-5; E=low; N=3
for r in $(seq $N); do for t in t1 t2 t3 t4 t5; do for c in bare official; do
  echo "runner/run.sh $t claude $M $E $c $r"; done; done; done | xargs -P 4 -L 1 env
python3 grader/grade.py results/raw results
```

That is 30 runs for n=3. Keep `-P` low on a busy machine; we only look at pass/fail, so latency does not matter. Our four arms ran in this exact way (120 runs).

## Adding another model or CLI

- Another model on Claude Code or Codex: nothing to change. Pass its model id and effort. The grader finds every arm id in the file names, ours first, the rest sorted.
- Another CLI: in `runner/run.sh` the `cc()` function (Claude Code) and the `codex)` branch of the final `case $cli in` are the two launchers. Add a branch that writes the CLI's raw output to `$O.jsonl`, then writes the final answer to `$O.txt`, and calls `runner/extract.py <kind> $O.jsonl $O.txt $O.tools`. `extract.py` is the hook: add a kind there that returns the final answer text and a `{tool name: count}` map. The `SBX` array holds the sandbox mounts; add the new binary and its read-only credentials there.
- Answer format: tasks ask for `=== FILE: <path> ===` blocks followed by `=== END ===`. The grader only reads that final text, so any CLI that returns it works.

## Grading and comparing with our table

`grader/grade.py` is static: it parses the files out of the answer and applies regex/AST-style checks, `P_*` for the pitfall checks and `B_*` for basic sanity checks. Nothing is executed. The per-arm and per-check tables are printed and also saved (`results/summary.txt` is that output for our runs). To compare, put your arm's `bare`/`official` pass counts next to the rows in the README table. Both are out of 45 pitfall checks per environment at n=3.

## What a run costs (from our raw results)

Token counts were not kept (the raw JSONL transcripts are not committed), so we cannot give them. What we can compute from `results/raw` over the 15 runs per cell:

| Arm | Mean answer size, bare / official (bytes) | Mean tool calls per run, bare / official |
| --- | --- | --- |
| `claude-opus-5-5@medium` | 3459 / 3622 | 0 / 0.93 |
| `claude-sonnet-5-5@high` | 3014 / 3135 | 0 / 0.87 |
| `claude-haiku-5-5@xhigh` | 2879 / 3253 | 0 / 4.67 |
| `gpt-6.1-sol@high` | 3097 / 2495 | 0.67 / 2.13 |

Tool calls are MCP/skill/Read calls for Claude Code; for Codex they are shell commands (its sandbox has a shell even in `bare`).

## Limits

- n is small: 3 runs per cell, 45 pitfall checks per arm and environment. One check flipping moves a score by about 2 points; do not read differences of one or two checks as a ranking.
- Static grading only. A pass means the answer avoids the pattern we flag, not that the code runs.
- Isolation is what makes `bare` mean "model memory only". It relies on `bwrap` and the clean config dirs from `setup.sh`; on another setup, check that your CLI does not read skills or rules from outside the sandbox (Codex scans `~/.agents/skills` regardless of `CODEX_HOME`, which is why `$HOME` is masked).
- CLI and model behavior drift. Record the CLI versions next to your results, as the README does.
