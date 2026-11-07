#!/usr/bin/env bash
# Usage: runner/run.sh <task:t1..t5> <arm> <cond:bare|official> <rep>
# arms: opus55-medium | sonnet55-high | haiku55-xhigh | gpt61sol-high
#
# Every run happens inside bubblewrap with $HOME replaced by an empty tmpfs, so the agent cannot
# read any local rules, skills, or repos (codex scans ~/.agents/skills regardless of CODEX_HOME).
# Only the CLI binaries, read-only credentials, the arm's own config dir and an empty work dir are mounted.
#
# Required env:
#   CLAUDE_BIN   path to the native Claude Code binary (not a wrapper script)
#   CODEX_PKG    path to the codex npm package dir that contains vendor/.../bin/codex
set -u
ROOT=$(cd "$(dirname "$0")/.." && pwd); S=$ROOT/.sandbox; RAW=$ROOT/results/raw
t=$1; arm=$2; cond=$3; rep=$4; N=${t}__${arm}__${cond}__${rep}; O=$RAW/$N; W=$S/work/$N
[ -s "$O.txt" ] && exit 0
: "${CLAUDE_CREDENTIALS:=$HOME/.claude/.credentials.json}"; : "${CODEX_AUTH:=$HOME/.codex/auth.json}"
CX=$(find "$CODEX_PKG" -path '*vendor/*/bin/codex' -type f | head -1)
P=$(cat "$ROOT/tasks/$t.txt"); mkdir -p "$W" "$RAW"
if [ "$cond" = bare ]; then CCD=$S/cc-bare; CXH=$S/codex-bare; else CCD=$S/cc-official; CXH=$S/codex-official; fi
SBX=(bwrap --ro-bind / / --tmpfs "$HOME" --tmpfs /tmp --dev /dev --proc /proc
  --ro-bind "$CLAUDE_BIN" "$CLAUDE_BIN" --ro-bind "$CODEX_PKG" "$CODEX_PKG"
  --ro-bind "$CLAUDE_CREDENTIALS" "$CLAUDE_CREDENTIALS" --ro-bind "$CODEX_AUTH" "$CODEX_AUTH"
  --bind "$CCD" "$CCD" --bind "$CXH" "$CXH" --bind "$W" "$W" --ro-bind "$S/official-mcp.json" "$S/official-mcp.json"
  --setenv HOME "$HOME" --chdir "$W" --die-with-parent)
s=$(date +%s)
cc() {
  if [ "$cond" = bare ]; then extra=(--safe-mode --tools ''); else
    extra=(--strict-mcp-config --mcp-config "$S/official-mcp.json" --tools "Skill,Read"
           --allowedTools "mcp__nuxt,mcp__nuxt-ui,mcp__nuxthub,Skill,Read" --permission-mode dontAsk); fi
  timeout 900 "${SBX[@]}" --setenv CLAUDE_CONFIG_DIR "$CCD" "$CLAUDE_BIN" -p "$P" --model "$1" --effort "$2" "${extra[@]}" \
    --output-format stream-json --verbose --no-session-persistence < /dev/null > "$O.jsonl" 2> "$O.err"
  python3 -I "$ROOT/runner/extract.py" claude "$O.jsonl" "$O.txt" "$O.tools"
}
case $arm in
  opus55-medium) cc claude-opus-5-5 medium;;
  sonnet55-high) cc claude-sonnet-5-5 high;;
  haiku55-xhigh) cc claude-haiku-5-5 xhigh;;
  gpt61sol-high)
    timeout 900 "${SBX[@]}" --setenv CODEX_HOME "$CXH" "$CX" exec -s read-only --skip-git-repo-check -m gpt-6.1-sol \
      -c model_reasoning_effort=high --json -o "$W/_out.txt" "$P" < /dev/null > "$O.jsonl" 2> "$O.err"
    cp "$W/_out.txt" "$O.txt" 2>/dev/null
    python3 -I "$ROOT/runner/extract.py" codex "$O.jsonl" "$O.txt" "$O.tools";;
esac
echo "$N secs=$(( $(date +%s)-s )) bytes=$(wc -c < "$O.txt" 2>/dev/null)" >> "$RAW/_log"
