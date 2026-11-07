"""Pull the final answer and the tool calls out of a Claude Code / Codex JSONL transcript."""
import json, sys, collections
kind, src, out_txt, out_tools = sys.argv[1:5]
tools = collections.Counter(); res = None
for line in open(src, encoding='utf-8', errors='replace'):
    try: d = json.loads(line)
    except Exception: continue
    if kind == 'claude':
        if d.get('type') == 'assistant':
            for b in d['message'].get('content', []):
                if b.get('type') == 'tool_use':
                    extra = b['input'].get('skill', b['input'].get('file_path', '')) if b['name'] in ('Skill', 'Read') else ''
                    tools[b['name'] + (':' + str(extra) if extra else '')] += 1
        if d.get('type') == 'result': res = d.get('result', '')
    else:
        it = d.get('item') or {}
        if d.get('type') == 'item.completed' and it.get('type') == 'mcp_tool_call': tools[it.get('server', '') + ':' + it.get('tool', '')] += 1
        if d.get('type') == 'item.completed' and it.get('type') == 'command_execution': tools['shell:' + it.get('command', '')[-160:]] += 1
if res is not None: open(out_txt, 'w').write(res)
open(out_tools, 'w').write(json.dumps(tools, ensure_ascii=False))
