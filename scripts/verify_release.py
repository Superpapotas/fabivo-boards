"""Scan an explicit release folder. Never print a matched value."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import re

PATTERNS = [
    rb'hf_[A-Za-z0-9]{20,}', rb'gh[pousr]_[A-Za-z0-9]{20,}',
    rb'github_pat_[A-Za-z0-9_]{30,}', rb'sk-[A-Za-z0-9_-]{20,}',
    rb'ak-[A-Za-z0-9]{20,}', rb'as-[A-Za-z0-9]{20,}',
    rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
    rb'(?i)(?:api_key|access_token|password|secret)\s*[:=]\s*[\x22\x27][A-Za-z0-9_./+\-=]{16,}[\x22\x27]',
]
FORBIDDEN = {'.env', '.env.local', 'auth.json', 'token', '.modal.toml', 'credentials', 'kaggle.json'}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('root', type=Path)
    args = ap.parse_args()
    hits = []
    count = 0
    for path in sorted(args.root.rglob('*')):
        if not path.is_file() or any(p in ['.git', '__pycache__'] for p in path.relative_to(args.root).parts):
            continue
        rel = str(path.relative_to(args.root))
        if path.name in FORBIDDEN: hits.append(rel + ': forbidden filename')
        data = path.read_bytes()
        if any(re.search(pattern, data) for pattern in PATTERNS): hits.append(rel + ': credential pattern')
        if 'open028' in rel.lower() or 'u100' in rel.lower(): hits.append(rel + ': excluded case filename')
        if path.suffix == '.py': ast.parse(data, filename=rel)
        count += 1
    # Do not print raw matches or file contents.
    print(json.dumps({'files_scanned': count, 'failures': hits, 'credential_values_printed': False}, indent=2))
    raise SystemExit(1 if hits else 0)

if __name__ == '__main__':
    main()
