#!/usr/bin/env python3
"""Patch image paths into game JSONs and rebuild manifest."""
import json, sys
from pathlib import Path
from datetime import datetime, timezone

repo = Path(sys.argv[1] if len(sys.argv) > 1 else '.')
games_dir  = repo / 'games'
data_dir   = repo / 'data'
shot_dir   = repo / 'images' / 'screenshots'
logo_dir   = repo / 'images' / 'logos'

def find_img(base, gid):
    if not base.exists(): return ''
    for ext in ('.jpg','.jpeg','.png','.webp','.gif'):
        if (base / f'{gid}{ext}').exists():
            return f'images/{base.name}/{gid}{ext}'
    return ''

patched = 0
for gf in games_dir.glob('*.json'):
    g = json.loads(gf.read_text(encoding='utf-8'))
    gid = g['id']
    shot = find_img(shot_dir, gid)
    logo = find_img(logo_dir, gid)
    changed = False
    if shot != g.get('screenshot',''):
        g['screenshot'] = shot; changed = True
    if logo != g.get('logo',''):
        g['logo'] = logo; changed = True
    if changed:
        gf.write_text(json.dumps(g, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
        patched += 1
print(f'games patched: {patched}')

# rebuild manifest from the patched game files
games = {}
for gf in games_dir.glob('*.json'):
    g = json.loads(gf.read_text(encoding='utf-8'))
    games[g['id']] = g

lists = {}
for lf in (data_dir / 'lists').glob('*.json'):
    lists[lf.stem] = json.loads(lf.read_text(encoding='utf-8'))['ids']

series = {}
for sf in (data_dir / 'series').glob('*.json'):
    s = json.loads(sf.read_text(encoding='utf-8'))
    series[s['id']] = s

series_order = json.loads((data_dir / 'series_order.json').read_text(encoding='utf-8'))['order']

now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
manifest = {'version': 2, 'updated': now, 'games': games, 'lists': lists, 'series': series, 'series_order': series_order}
(data_dir / 'manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
print(f'manifest rebuilt: {len(games)} games, {len(lists)} lists, {len(series)} series')