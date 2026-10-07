"""Fetch authorized original URLs and report missing or changed images.

This script does not grant rights to use third-party images. It never stores a
failed-hash download. Training copies may have been resized or re-encoded.
"""
import argparse
import hashlib
import json
from pathlib import Path
import urllib.request
from urllib.parse import urlsplit


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('manifest', type=Path)
    ap.add_argument('output', type=Path)
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    failed = False
    for line in args.manifest.read_text().splitlines():
        row = json.loads(line)
        if row['family'] not in ['real', 'pl', 'photo', 'boxed', 'h48']:
            continue
        url = row.get('source_image_url')
        if not url:
            print(row['case'], 'missing-url')
            failed = True
            continue
        parts = urlsplit(url)
        if parts.scheme not in ['https', 'http'] or parts.username or parts.password:
            print(row['case'], 'invalid-url')
            failed = True
            continue
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'fabivo-boards-research/1.0'})
            with urllib.request.urlopen(req, timeout=30) as response:
                data = response.read(32 * 1024 * 1024 + 1)
            if len(data) > 32 * 1024 * 1024:
                print(row['case'], 'too-large')
                failed = True
                continue
        except Exception:
            # Do not print exception text. URLs can carry private query values.
            print(row['case'], 'missing-or-unavailable')
            failed = True
            continue
        actual = hashlib.sha256(data).hexdigest()
        expected = row.get('source_file_sha256') or row['used_image_sha256']
        if actual != expected:
            print(row['case'], 'changed', actual)
            failed = True
            continue
        if actual != row['used_image_sha256']:
            print(row['case'], 'original-verified-training-copy-was-transformed')
        folder = args.output / row['split']
        folder.mkdir(exist_ok=True)
        (folder / (row['case'] + '.jpg')).write_bytes(data)
        print(row['case'], 'verified')
    raise SystemExit(1 if failed else 0)

if __name__ == '__main__':
    main()
