"""Mechanical grader for the five Nuxt pitfall tasks.

Usage: python3 grader/grade.py [RUNS_DIR] [OUT_DIR]
Each run output is a text file named <task>__<arm>__<cond>__<rep>.txt containing
`=== FILE: <path> ===` blocks. Checks prefixed P_ are the pitfall itself; B_ are basic completeness.
"""
import re, sys, json, os, glob
def parse_files(text):
    files = {}; cur = None; buf = []
    for line in text.splitlines():
        m = re.match(r'^\s*=== FILE:\s*(.+?)\s*===\s*$', line)
        if m or re.match(r'^\s*=== END ===\s*$', line):
            if cur: files[cur] = '\n'.join(buf)
            cur = m.group(1).strip('`') if m else None; buf = []; continue
        if cur is not None: buf.append(line)
    if cur: files[cur] = '\n'.join(buf)
    # strip code fences
    for k, v in files.items():
        v = re.sub(r'^\s*```[\w-]*\s*\n', '', v); v = re.sub(r'\n\s*```\s*$', '', v.rstrip())
        files[k] = v
    return files
def find(files, suffix):
    for k, v in files.items():
        if k.replace('\\', '/').endswith(suffix): return v
    return None
def strip_comments(s):
    s = re.sub(r'<!--.*?-->', '', s, flags=re.S); s = re.sub(r'/\*.*?\*/', '', s, flags=re.S)
    return re.sub(r'(^|[^:])//[^\n]*', r'\1', s)
def element_inner(src, tag):
    i = src.find('<' + tag)
    if i < 0: return None, None
    j = src.find('>', i); open_tag = src[i:j+1]
    if open_tag.endswith('/>'): return open_tag, ''
    depth = 1; pos = j + 1; pat = re.compile(r'<(/?)' + tag + r'\b[^>]*?(/?)>')
    for m in pat.finditer(src, pos):
        if m.group(2): continue
        depth += -1 if m.group(1) else 1
        if depth == 0: return open_tag, src[j+1:m.start()]
    return open_tag, src[j+1:]
def top_level_nontemplate(inner):
    # remove top-level <template ...>...</template> blocks (depth aware)
    out = []; i = 0; depth = 0
    for m in re.finditer(r'<(/?)template\b[^>]*?(/?)>', inner):
        if m.group(2): continue
        if not m.group(1):
            if depth == 0: out.append(inner[i:m.start()])
            depth += 1
        else:
            depth -= 1
            if depth == 0: i = m.end()
    if depth == 0: out.append(inner[i:])
    return ''.join(out).strip()
def slot_block(inner, name):
    m = re.search(r'<template\s+(?:#|v-slot:)' + name + r'\b[^>]*>', inner)
    if not m: return None
    depth = 1
    for t in re.finditer(r'<(/?)template\b[^>]*?(/?)>', inner[m.end():]):
        if t.group(2): continue
        depth += -1 if t.group(1) else 1
        if depth == 0: return inner[m.end(): m.end()+t.start()]
    return inner[m.end():]

def g1(f):
    v = find(f, 'DeleteUserModal.vue'); c = {}
    if not v: return {'file_present': False}
    v = strip_comments(v); ot, inner = element_inner(v, 'UModal')
    if ot is None: return {'file_present': True, 'uses_umodal': False}
    body = slot_block(inner, 'body'); content = slot_block(inner, 'content')
    loose = top_level_nontemplate(inner)
    c['P_body_in_#body'] = bool(body and 'UInput' in body) or bool(content and 'UInput' in content)
    c['P_no_stray_children'] = (loose == '') or (not body and not content and 'UInput' not in loose)
    c['P_width_via_ui'] = bool(re.search(r':ui\s*=\s*"[^"]*max-w-2xl', ot)) or bool(re.search(r'max-w-2xl', v) and re.search(r':ui\s*=', ot) and not re.search(r'\sclass\s*=\s*"[^"]*max-w', ot))
    c['P_no_class_width'] = not re.search(r'\sclass\s*=\s*"[^"]*max-w', ot)
    c['B_title_prop'] = bool(re.search(r'\s:?title\s*=', ot)) or bool(slot_block(inner, 'title'))
    c['B_footer_slot'] = bool(slot_block(inner, 'footer'))
    return c
def g2(f):
    c = {}; p = find(f, 'orders.vue'); pl = find(f, 'plugins/api.ts') or find(f, 'api.ts')
    if p:
        p = strip_comments(p)
        c['P_no_toplevel_await_$fetch'] = not re.search(r'^(?:const|let|var)?[^\n]*?\bawait\s+\$fetch\(', p, re.M) or all(l.startswith((' ', '\t')) for l in re.findall(r'^[^\n]*await\s+\$fetch\(', p, re.M))
        bad_key = False
        for m in re.finditer(r'useAsyncData\(\s*([^,]+?),', p):
            a = m.group(1)
            if re.search(r'page|sort|query', a) and not re.match(r"^\s*['\"][^'\"$]*['\"]\s*$", a): bad_key = True
        for m in re.finditer(r'\bkey\s*:\s*([^,\n}]+)', p):
            if re.search(r'page|sort|query', m.group(1)) and not re.match(r"^\s*['\"][^'\"$]*['\"]\s*$", m.group(1)): bad_key = True
        c['P_key_excludes_page_sort'] = not bad_key
        c['B_uses_useFetch_or_AsyncData'] = bool(re.search(r'use(Fetch|AsyncData|LazyFetch|LazyAsyncData)\s*(<[^>]*>)?\s*\(', p))
    if pl:
        pl = strip_comments(pl)
        c['P_no_global_$fetch_override'] = not re.search(r'globalThis\.\$fetch\s*=|(?<![.\w])\$fetch\s*=(?!=)|window\.\$fetch\s*=', pl)
        c['B_plugin_uses_create_or_hook'] = bool(re.search(r'\$fetch\.create|ofetch|onRequest', pl))
    return c
def g3(f):
    c = {}; u = find(f, '[id].patch.ts'); d = find(f, 'dashboard.get.ts'); n = find(f, 'nuxt.config.ts')
    if u:
        u = strip_comments(u)
        setarg = re.search(r'\.set\(\s*([^)]*?)\)', u, re.S)
        sa = setarg.group(1) if setarg else ''
        passthrough = bool(re.search(r'passthrough\(|catchall\(|z\.record\(|z\.any\(\)|looseObject', u))
        raw = bool(re.search(r'readBody\(', u))
        c['P_no_mass_assignment'] = not passthrough and not raw and not re.search(r'role|passwordHash', sa)
        c['P_authz_self_only'] = 'requireUserSession' in u and (bool(re.search(r"statusCode:\s*403|Forbidden|forbidden", u)) or bool(re.search(r"eq\(\s*users\.id\s*,\s*[\w.]*(user|session)[\w.]*\.id", u)))
    if d:
        d = strip_comments(d)
        cached_handler = bool(re.search(r'(define)?[Cc]achedEventHandler\(', d))
        cached_fn = bool(re.search(r'[Cc]achedFunction\(', d))
        getkey_user = bool(re.search(r'getKey[\s\S]{0,400}?(user|session)', d, re.I))
        if cached_handler:
            c['P_cache_key_has_user'] = getkey_user
        elif cached_fn:
            # function cache: safe when the key is derived from the user id (getKey or the argument itself)
            c['P_cache_key_has_user'] = getkey_user or not re.search(r'getKey', d)
        else:
            c['P_cache_key_has_user'] = True
        c['B_has_cache'] = bool(re.search(r'[Cc]ached(EventHandler|Function)\(|useStorage\(', d))
    if n:
        n = strip_comments(n)
        c['P_apiBase_public'] = bool(re.search(r'public\s*:\s*\{[^}]*apiBase', n, re.S)) and not re.search(r'runtimeConfig\s*:\s*\{\s*apiBase', n)
    return c
def g4(f):
    c = {}; n = find(f, 'nuxt.config.ts'); s = find(f, 'stats.get.ts')
    if n:
        n = strip_comments(n)
        has_d1 = re.search(r"driver\s*:\s*['\"]d1['\"]", n)
        guarded = re.search(r'NODE_ENV|NITRO_PRESET|nuxt\.options\.dev|import\.meta\.dev|\$production|\$development|process\.env\.CF_', n)
        c['P_d1_driver_not_unconditional'] = (not has_d1) or bool(guarded)
        c['B_hub_db_config'] = bool(re.search(r'hub\s*:\s*\{[\s\S]*?(db|database)\s*:', n))
    if s:
        s = strip_comments(s)
        aliases = re.findall(r"\.as\(\s*['\"]([\w]+)['\"]\s*\)", s)
        col_aliases = [a for a in aliases if not re.search(r'^(m|t|mc|tc|members?|tasks?|member_?counts?|task_?counts?|sub\w*|\w+_sq|\w+Sq|\w+Sub|\w+Counts?)$', a) or a.lower() in ('count', 'cnt', 'total', 'c', 'n', 'value')]
        dup = len(aliases) != len(set(aliases))
        generic_dup = sum(1 for a in aliases if a.lower() in ('count', 'cnt', 'total', 'c', 'n', 'value')) >= 2
        c['P_subquery_alias_unique'] = not dup and not generic_dup
        c['B_uses_subquery'] = bool(re.search(r'\.as\(|sql`\s*\(\s*select', s, re.I))
    return c
def g5(f):
    c = {}; n = find(f, 'nuxt.config.ts'); w = find(f, 'stripe.post.ts')
    if n:
        n = strip_comments(n)
        c['P_webhook_csrf_exempt'] = bool(re.search(r"['\"]/api/webhooks?(/\*\*|/stripe)?['\"]\s*:\s*\{[^}]*?(csurf\s*:\s*false|csrf\s*:\s*false)", n, re.S)) or bool(re.search(r'csurf\s*:\s*\{[^}]*exclude[^}]*webhook', n, re.S))
        ws = re.search(r"['\"]wss?:", n)
        dev_guard = bool(re.search(r'import\.meta\.dev|NODE_ENV|nuxt\.options\.dev|\$development|isDev|process\.dev', n))
        dev_csp_off = bool(re.search(r'\$development\s*:\s*\{[\s\S]*?contentSecurityPolicy\s*:\s*false', n))
        c['P_hmr_ws_dev_only'] = (bool(ws) and dev_guard) or dev_csp_off
        c['B_csrf_still_on'] = bool(re.search(r'csrf\s*:\s*true', n))
    if w:
        w = strip_comments(w)
        c['B_raw_body_signature'] = bool(re.search(r'readRawBody\(', w)) and bool(re.search(r'constructEvent(Async)?\(|createHmac\(|crypto\.subtle|subtle\.(sign|verify|importKey)', w))
    return c
G = {'t1': g1, 't2': g2, 't3': g3, 't4': g4, 't5': g5}
if __name__ == '__main__':
    import collections
    RUNS = sys.argv[1] if len(sys.argv) > 1 else 'results/raw'
    OUT = sys.argv[2] if len(sys.argv) > 2 else 'results'
    rows = []
    for out in sorted(glob.glob(os.path.join(RUNS, '*.txt'))):
        name = os.path.basename(out)[:-4]; parts = name.split('__')
        if len(parts) != 4: continue
        t, arm, cond, rep = parts
        files = parse_files(open(out, encoding='utf-8', errors='replace').read())
        tools = {}
        tp = out[:-4] + '.tools'
        if os.path.exists(tp):
            try: tools = json.load(open(tp))
            except Exception: pass
        rows.append({'task': t, 'arm': arm, 'cond': cond, 'rep': rep, 'nfiles': len(files), 'checks': G[t](files), 'tools': tools})
    json.dump(rows, open(os.path.join(OUT, 'graded.json'), 'w'), ensure_ascii=False, indent=1)
    agg = collections.defaultdict(lambda: [0, 0]); aggB = collections.defaultdict(lambda: [0, 0]); per = collections.defaultdict(lambda: [0, 0])
    for r in rows:
        for k, v in r['checks'].items():
            tgt = agg if k.startswith('P_') else aggB
            tgt[(r['arm'], r['cond'])][0] += int(bool(v)); tgt[(r['arm'], r['cond'])][1] += 1
            if k.startswith('P_'): per[(r['task'], k, r['arm'], r['cond'])][0] += int(bool(v)); per[(r['task'], k, r['arm'], r['cond'])][1] += 1
    arms = ['claude-opus-5-5@medium', 'claude-sonnet-5-5@high', 'claude-haiku-5-5@xhigh', 'gpt-6.1-sol@high']; conds = ['bare', 'official']
    print('== pitfall checks passed (P_*), by arm x cond')
    for a in arms: print(a.ljust(26), '  '.join(f"{c}:{agg[(a,c)][0]}/{agg[(a,c)][1]}" for c in conds), ' | basic', '  '.join(f"{c}:{aggB[(a,c)][0]}/{aggB[(a,c)][1]}" for c in conds))
    print('== per check (bare / official)')
    keys = sorted({(k[0], k[1]) for k in per})
    print('check'.ljust(38) + ''.join(a.rjust(30) for a in arms))
    for t, k in keys:
        print(f"{t} {k}".ljust(38) + ''.join(f"{per[(t,k,a,'bare')][0]}/{per[(t,k,a,'bare')][1]} {per[(t,k,a,'official')][0]}/{per[(t,k,a,'official')][1]}".rjust(30) for a in arms))
    print('== tool use in official cond (runs using any MCP / skill)')
    for a in arms:
        rs = [r for r in rows if r['arm'] == a and r['cond'] == 'official']
        mcp = sum(1 for r in rs if any(('mcp' in k or k.split(':')[0] in ('nuxt', 'nuxt-ui', 'nuxthub')) for k in r['tools']))
        sk = sum(1 for r in rs if any(('Skill' in k or 'SKILL.md' in k or 'skills/nuxt-ui' in k) for k in r['tools']))
        print(a.ljust(26), f"runs={len(rs)} mcp_used={mcp} skill_used={sk}")
