#!/usr/bin/env bash
# Builds the clean config dirs used by run.sh under ./.sandbox
#   bare      : no CLAUDE.md, no skills, no MCP
#   official  : only the official Nuxt MCP servers + the nuxt-ui skill shipped in github.com/nuxt/ui
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd); S=$ROOT/.sandbox
: "${CLAUDE_CREDENTIALS:=$HOME/.claude/.credentials.json}"
: "${CODEX_AUTH:=$HOME/.codex/auth.json}"
mkdir -p "$S"/{cc-bare,cc-official/skills,codex-bare,codex-official/skills,work,official}
for d in cc-bare cc-official; do ln -sfn "$CLAUDE_CREDENTIALS" "$S/$d/.credentials.json"; done
for d in codex-bare codex-official; do ln -sfn "$CODEX_AUTH" "$S/$d/auth.json"; done
if [ ! -d "$S/official/ui" ]; then
  git clone -q --depth 1 --filter=blob:none --sparse https://github.com/nuxt/ui "$S/official/ui"
  git -C "$S/official/ui" sparse-checkout set skills
fi
git -C "$S/official/ui" log -1 --format='nuxt/ui skills @ %h (%ad)' --date=short
rm -rf "$S/cc-official/skills/nuxt-ui" "$S/codex-official/skills/nuxt-ui"
cp -r "$S/official/ui/skills/nuxt-ui" "$S/cc-official/skills/"; cp -r "$S/official/ui/skills/nuxt-ui" "$S/codex-official/skills/"
cat > "$S/official-mcp.json" <<'J'
{"mcpServers":{"nuxt":{"type":"http","url":"https://nuxt.com/mcp"},"nuxt-ui":{"type":"http","url":"https://ui.nuxt.com/mcp"},"nuxthub":{"type":"http","url":"https://hub.nuxt.com/mcp"}}}
J
printf 'model = "gpt-6.1-sol"\n' > "$S/codex-bare/config.toml"
cat > "$S/codex-official/config.toml" <<'T'
model = "gpt-6.1-sol"
approval_policy = "never"
[mcp_servers.nuxt]
url = "https://nuxt.com/mcp"
[mcp_servers.nuxt-ui]
url = "https://ui.nuxt.com/mcp"
[mcp_servers.nuxthub]
url = "https://hub.nuxt.com/mcp"
T
echo "sandbox ready: $S"
