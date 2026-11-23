#!/usr/bin/env python3
"""
LBDB converter — reads LaunchBox Metadata.zip (or Metadata.xml),
trims to fields the Co-Op Vault admin needs, writes compact JSON.

Usage:
    python convert.py <Metadata.zip|Metadata.xml> <output.json>
"""

import sys, json, zipfile, datetime
import xml.etree.ElementTree as ET

REGION_PREF = {
    'North America': 6,
    'World': 5,
    'United States': 4,
    'Europe': 3,
    '': 2,
    'United Kingdom': 1,
}


def parse_xml(xml_stream):
    games = []
    by_id = {}
    logo_rank = {}
    shot_rank = {}

    context = ET.iterparse(xml_stream, events=('end',))
    for _, elem in context:
        if elem.tag == 'Game':
            name     = (elem.findtext('Name') or '').strip()
            platform = (elem.findtext('Platform') or '').strip()
            dbid     = (elem.findtext('DatabaseID') or '').strip()
            if not name or not platform:
                elem.clear()
                continue

            dev = (elem.findtext('Developer') or '').strip()
            pub = (elem.findtext('Publisher') or '').strip()
            rel = (elem.findtext('ReleaseDate') or elem.findtext('ReleaseYear') or '').strip()

            entry = {'n': name, 'p': platform}
            if dev: entry['dev'] = dev
            if pub: entry['pub'] = pub
            if rel: entry['rel'] = rel
            games.append(entry)
            if dbid:
                by_id[dbid] = entry
            elem.clear()

        elif elem.tag == 'GameImage':
            dbid = (elem.findtext('DatabaseID') or '').strip()
            entry = by_id.get(dbid)
            if entry is not None:
                img_type = (elem.findtext('Type') or '').strip()
                fn = (elem.findtext('FileName') or '').strip()
                if fn and img_type in ('Clear Logo', 'Screenshot - Gameplay'):
                    region = (elem.findtext('Region') or '').strip()
                    rank = REGION_PREF.get(region, 0)
                    if img_type == 'Clear Logo':
                        if rank > logo_rank.get(dbid, -1):
                            logo_rank[dbid] = rank
                            entry['logo'] = fn
                    else:
                        if rank > shot_rank.get(dbid, -1):
                            shot_rank[dbid] = rank
                            entry['screenshot'] = fn
            elem.clear()

    return games


def convert(src_path, out_path):
    if src_path.lower().endswith('.zip'):
        with zipfile.ZipFile(src_path) as z:
            with z.open('Metadata.xml') as xml_stream:
                games = parse_xml(xml_stream)
    else:
        with open(src_path, 'rb') as xml_stream:
            games = parse_xml(xml_stream)

    payload = {
        'generated': datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z'),
        'count': len(games),
        'games': games,
    }

    raw = json.dumps(payload, ensure_ascii=False, separators=(',', ':'))
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(raw)

    size_mb = round(len(raw.encode('utf-8')) / 1024 / 1024, 1)
    logos = sum(1 for g in games if 'logo' in g)
    shots = sum(1 for g in games if 'screenshot' in g)
    print(f"Wrote {len(games)} games ({logos} logos, {shots} shots) to {out_path} (~{size_mb} MB)")


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: convert.py <Metadata.zip|Metadata.xml> <output.json>")
        sys.exit(1)
    convert(sys.argv[1], sys.argv[2])
