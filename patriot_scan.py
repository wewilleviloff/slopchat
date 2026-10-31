# -*- coding: utf-8 -*-
import json, re, unicodedata
from collections import defaultdict

data = json.load(open('/workspace/all_msgs.json', encoding='utf-8'))

# load known users
users = [l.strip() for l in open('/workspace/chat_people.txt', encoding='utf-8') if l.strip() and not l.startswith('#')]
def norm_name(s):
    s = unicodedata.normalize('NFKC', s)
    s = re.sub(r'\u200e|\u2063|\u200f|\u202a|\u200b', '', s)
    return s.strip()
user_set = set(norm_name(u) for u in users)

RU_TERMS = [
 # pro-russia / patriotic
 (r'\bкрым\b.{0,40}\b(наш|вернули|россия|наш)\b', 3, 'Крым наш'),
 (r'(наш|вернули).{0,30}\bкрым\b', 3, 'Крым наш'),
 (r'\bкрымнаш', 3, ''),
 (r'\bза росси', 3, ''),
 (r'\bроссия вперёд|\bроссия вперед', 3, ''),
 (r'\bмы — россия|\bмы - россия|\bмы россия\b', 3, ''),
 (r'\bвеликая россия|\bмогучая россия', 2, ''),
 (r'\bдержав', 1, ''),
 (r'\bпобеда будет за нами|\bпобеда за нами', 2, ''),
 (r'\bz\s*операция|\bсвои?\b.{0,15}(бойцы|парни|ребята)', 1, ''),
 (r'\bdnr|\bлнр|\bднр|\bлнр\b', 1, ''),
 (r'(донбасс).{0,30}(наш|россия|за)', 2, ''),
 (r'\bнаши бойцы|\bнаши парни|\bнаших ребят', 2, ''),
 (r'\bпатриот', 1, ''),
 (r'\bроссийск', 0, ''),  # neutral mention counted separately
 (r'\bроссия\b', 0, ''),
 (r'\bродин', 1, ''),
 (r'\bфлаг россии|триколор', 1, ''),
 (r'\bсталин.*велик|\bвелик.*сталин', 1, ''),
 (r'\bslavua|slava ukraini|герої не|і слава', 0, ''),
]
ANTI_RU = [
 (r'\bпутин.{0,40}(войска|напал|убил|агрессор|террорист|фашист)', 3, 'анти-Putin'),
 (r'(напал|агрессор|оккупант|террористы?).{0,30}(росси|путин|вв)', 3, ''),
 (r'\bроссия.{0,30}(фашист|империя зла|террорист|оккупант)', 3, ''),
 (r'\bхохл|~~~москал|ватники? (нет|долой)', 0, ''),
 (r'\bкрым.{0,40}(украин|не наш)', 3, 'Крым не наш'),
 (r'(украин|україна).{0,30}(наш|правда|побед|законна)', 3, ''),
]
FOREIGN_SYMP = {
 'Украина': [r'\bукраин[аеыу]?й?\b', r'\bукраїна', r'\bльвов', r'\bкиев', r'\bодесс'],
 'Грузия': [r'\bгрузи', r'\bтбилис', r'\bсакартвел'],
 'Армения': [r'\bармян', r'\bереван'],
 'Азербайджан': [r'\bазербайджан', r'\bбаку\b'],
 'Казахстан': [r'\bказах', r'\bалматы', r'\bастана'],
 'Беларусь': [r'\bбелорус', r'\bминск', r'\bбеларус'],
 'Германия': [r'\bнемц[еы]|\bгермани|\bберлин'],
 'Франция': [r'\bфранц|париж'],
 'Италия': [r'\bитали|\bрим\b|\bмилан'],
 'Испания': [r'\bиспани|\bмадрид|\bбарселон'],
 'Португалия': [r'\bпортугал'],
 'Турция': [r'\bтурци|\bтурции|стамбул|анталья'],
 'Таиланд': [r'\bтай(?:ланд)?\b|\bпхукет|\bпаттайа'],
 'Вьетнам': [r'\bвьетнам|\bда.?нанг|\bфукуок'],
 'Египет': [r'\bегипет|\bхургада|\bшарм'],
 'ОАЭ/Дубай': [r'\bдуба|\bоаэ|\bэмират'],
 'Кипр': [r'\bкипр'],
 'Греция': [r'\bгреци|\bафины|\bкрит\b'],
 'Индия': [r'\bинди[ия]|\bгоа\b|\bдели\b'],
 'Бали/Индонезия': [r'\bбали\b|\bиндонез'],
 'Япония': [r'\bяпони|\bтокио'],
 'Китай': [r'\bкита[ий]'],
 'Южная Корея': [r'\bкорей|\bсеул\b'],
 'США': [r'\bсша|\bамерики|\bштаты|\bнью.?йорк|\bкалифорни|\bтехас'],
 'Канада': [r'\bканад'],
 'Великобритания': [r'\ббритан|\bлондон'],
 'Польша': [r'\bпольш|\bваршав'],
 'Финляндия': [r'\bфинлянд|\bхельсинки'],
 'Норвегия': [r'\bнорвег|\bосло\b'],
 'Исландия': [r'\bисланд'],
 'Чехия': [r'\bчехи|\bпраг'],
 'Сербия': [r'\bсерби|\ббелград'],
 'Черногория': [r'\bчерногор'],
 'Хорватия': [r'\bхорват'],
 'Аргентина': [r'\bаргентин'],
 'Бразилия': [r'\bбразил'],
 'Мексика': [r'\bмексик'],
 'Уругвай': [r'\bуругва'],
 'Израиль': [r'\bизраил|\bтель.?авив'],
 'Марокко': [r'\bмарокк'],
 'Тунис': [r'\bтунис'],
 'Шри-Ланка': [r'\bшри.?ланк|\bцейлон'],
 'Мальдивы': [r'\bмальдив'],
 'Словакия': [r'\bсловац|\bбратислав'],
 'Венгрия': [r'\bвенгри|\bбудапешт'],
 'Австрия': [r'\bавстри|\bвен[а] \b'],
 'Нидерланды': [r'\bнидерланд|\bголланд|\bамстердам'],
 'Болгария': [r'\bболгари|\bсофи[яи] \b'],
 'Куба': [r'\bкуб[ау]\b|\bгаван'],
}
# fix accidental cyril typos in regexes
FOREIGN_SYMP['Великобритания'] = [r'британ|лондон']
FOREIGN_SYMP['Австрия'] = [r'австри']
FOREIGN_SYMP['Болгария'] = [r'болгар']
FOREIGN_SYMP['Куба'] = [r'\bкуба\b|гаван']

stats = defaultdict(lambda: {'msgs':0,'ru_neutral':0,'pro_ru':0,'anti_ru':0,
                             'foreign':defaultdict(int),'pro_examples':[],'anti_examples':[],'for_examples':defaultdict(list)})

def get_author(m):
    a = m.get('author') or m.get('sender') or ''
    return norm_name(a)

total=0
for m in data if isinstance(data,list) else []:
    pass

if isinstance(data, dict):
    msgs = data.get('messages', [])
else:
    msgs = data

for m in msgs:
    text = m.get('text')
    if not text: continue
    if isinstance(text, list):
        t = ''.join(x if isinstance(x,str) else x.get('text','') for x in text)
    else:
        t = text
    a = get_author(m)
    if a not in user_set: continue
    tl = t.lower()
    s = stats[a]; s['msgs']+=1
    for pat,w,label in RU_TERMS:
        if re.search(pat, tl):
            if w==0 and 'российск' in pat or 'россия\\b' in pat:
                s['ru_neutral']+=1
            else:
                s['pro_ru']+=1
                if len(s['pro_examples'])<3 and w>=2: s['pro_examples'].append(t[:120])
            break
    for pat,w,label in ANTI_RU:
        if re.search(pat, tl):
            s['anti_ru']+=1
            if len(s['anti_examples'])<3: s['anti_examples'].append(t[:120])
            break
    for country,pats in FOREIGN_SYMP.items():
        hit=False
        for p in pats:
            if re.search(p, tl):
                hit=True; break
        if hit:
            s['foreign'][country]+=1
            if len(s['for_examples'][country])<2:
                s['for_examples'][country].append(t[:120])

out=[]
for name,s in stats.items():
    out.append({'name':name, **{k:v for k,v in s.items() if k!='foreign' and k!='for_examples'},
                'foreign':dict(s['foreign']), 'for_ex':{k:v for k,v in s['for_examples'].items()}})
json.dump(out, open('/workspace/patriot_raw.json','w',encoding='utf-8'), ensure_ascii=False, indent=1)
print('users with msgs:', len(out))
for o in sorted(out, key=lambda x:-x['pro_ru']):
    top_for = sorted(o['foreign'].items(), key=lambda kv:-kv[1])[:4]
    print(f"{o['name']:24} msgs={o['msgs']:6} ru_ment={o['ru_neutral']:5} pro={o['pro_ru']:4} anti={o['anti_ru']:3} foreign={top_for}")
