#!/usr/bin/env python3
"""
LBDB converter — reads LaunchBox Metadata.zip, extracts Metadata.xml,
trims to just the fields the Co-Op Vault admin needs, writes compact JSON.

Usage:
    python convert.py <Metadata.zip> <output.json>

Field mapping (short keys keep the file ~30% smaller):
    n   = game name
    p   = platform
    dev = developer
    pub = publisher
    rel = release (YYYY-MM-DD or YYYY, whichever the source has)

Streaming parser — never builds the full XML tree, so a 500MB source
uses ~100MB of RAM instead of ~4GB.
"""

import sys, json, zipfile, datetime
import xml.etree.ElementTree as ET


def convert(zip_path, out_path):
    games = []
    with zipfile.ZipFile(zip_path) as z:
        with z.open('Metadata.xml') as xml_stream:
            context = ET.iterparse(xml_stream, events=('end',))
            for _, elem in context:
                if elem.tag != 'Game':
                    continue

                name     = (elem.findtext('Name') or '').strip()
                platform = (elem.findtext('Platform') or '').strip()
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

                elem.clear()

    payload = {
        'generated': datetime.datetime.utcnow().isoformat(timespec='seconds') + 'Z',
        'count': len(games),
        'games': games,
    }

    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, separators=(',', ':'))

    size_mb = round(len(json.dumps(payload, separators=(',', ':'))) / 1024 / 1024, 1)
    print(f"Wrote {len(games)} games to {out_path} (~{size_mb} MB)")


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: convert.py <Metadata.zip> <output.json>")
        sys.exit(1)
    convert(sys.argv[1], sys.argv[2])
