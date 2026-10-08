"""Check local documentation links and, optionally, tracked Git assets.

Run after git add and before publication:
python3 scripts/verify_document_links.py --require-tracked
"""
import argparse
from html.parser import HTMLParser
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.values = []

    def handle_starttag(self, tag, attrs):
        self.values.extend(value for key, value in attrs if key in ('href', 'src') and value)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--require-tracked', action='store_true')
    args = parser.parse_args()
    files = [ROOT/'README.md', *sorted((ROOT/'docs').glob('*.md')),
             *sorted((ROOT/'docs').glob('*.html')), *sorted((ROOT/'hf').rglob('README.md'))]
    tracked = set()
    if args.require_tracked:
        tracked = set(subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0'))
    checked = 0
    for source in files:
        text = source.read_text()
        if source.suffix == '.html':
            html = Links()
            html.feed(text)
            links = html.values
        else:
            links = re.findall(r'\]\(([^\s)]+)\)', text)
        for link in links:
            parsed = urlsplit(link)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            target = (source.parent/unquote(parsed.path)).resolve()
            relative = target.relative_to(ROOT)
            if not target.is_file():
                raise AssertionError(f'Missing link: {source.relative_to(ROOT)} -> {relative}')
            if args.require_tracked and relative.as_posix() not in tracked:
                raise AssertionError(f'Untracked link: {source.relative_to(ROOT)} -> {relative}')
            checked += 1
    print(f'Checked {checked} local document/image links' + (' against the Git index.' if args.require_tracked else '.'))


if __name__ == '__main__':
    main()
