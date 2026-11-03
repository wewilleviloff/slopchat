#!/usr/bin/env python3
"""Парсер HTML-экспорта Telegram: все сообщения, с привязкой имени автора к joined-сообщениям."""
import re, json, glob, html

def unesc(s):
    prev = None
    while s != prev:
        prev = s
        s = html.unescape(s)
    return s

split_re = re.compile(r'(<div class="message default clearfix(?: joined)?" id="message\d+">)')
date_re = re.compile(r'title="(\d{2}\.\d{2}\.\d{4} \d{2}:\d{2}:\d{2}) GMT')
name_re = re.compile(r'<div class="from_name">\s*(.*?)\s*</div>', re.S)
text_re = re.compile(r'<div class="text">\s*(.*?)\s*</div>', re.S)

out = []
for f in sorted(glob.glob('/workspace/ChatExport_2026-10-31/messages*.html')):
    src = open(f, encoding='utf-8').read()
    parts = split_re.split(src)
    last_name = None
    for i in range(1, len(parts), 2):
        head = parts[i]
        body = parts[i + 1] if i + 1 < len(parts) else ''
        joined = ' joined"' in head
        mid = int(re.search(r'id="message(\d+)"', head).group(1))
        d = date_re.search(body[:1500])
        if not d:
            continue
        nm = name_re.search(body[:2500])
        if nm:
            last_name = unesc(nm.group(1)).strip()
        elif not joined:
            last_name = None
        tx = text_re.search(body)
        txt = ''
        if tx:
            t = tx.group(1)
            t = re.sub(r'<br\s*/?>', '\n', t)
            t = re.sub(r'<[^>]+>', '', t)
            txt = unesc(t).strip()
        out.append({'author': last_name, 'dt': d.group(1), 'text': txt,
                    'file': f.split('/')[-1], 'id': mid})

print('total parsed:', len(out))
json.dump(out, open('/workspace/all_html_msgs.json', 'w'), ensure_ascii=False)
nov = [o for o in out if o['dt'][3:10] == '.11.2026']
print('november:', len(nov))
from collections import Counter
print(Counter(o['dt'][:10] for o in nov))
ar = [o for o in out if o['author'] and ('Артур' in o['author'] or 'Нехоч' in o['author'])]
print('arthur total:', len(ar), 'nov:', sum(1 for o in ar if o['dt'][3:10]=='.11.2026'))
