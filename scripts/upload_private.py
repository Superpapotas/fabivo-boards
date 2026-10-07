"""Upload an explicit, scanned staging folder. Never change visibility to public."""
import argparse
import hashlib
import json
from pathlib import Path
from huggingface_hub import HfApi, snapshot_download
from huggingface_hub.errors import RepositoryNotFoundError


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(8*1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('folder', type=Path)
    ap.add_argument('name')
    ap.add_argument('--type', default='model', choices=['model','dataset'])
    ap.add_argument('--verify-root', type=Path, required=True)
    args = ap.parse_args()
    api = HfApi()
    owner = api.whoami()['name']
    repo = owner + '/' + args.name
    try:
        info = api.repo_info(repo, repo_type=args.type)
        if not info.private:
            raise RuntimeError('Existing repository is not private; upload refused')
    except RepositoryNotFoundError:
        api.create_repo(repo, repo_type=args.type, private=True)
    if not api.repo_info(repo, repo_type=args.type).private:
        raise RuntimeError('Private visibility check failed')
    # No credential stores or source workspace are passed to upload_folder.
    files = {str(p.relative_to(args.folder)): digest(p) for p in args.folder.rglob('*')
             if p.is_file() and p.name != 'SHA256SUMS.json' and '.cache' not in p.parts}
    (args.folder / 'SHA256SUMS.json').write_text(json.dumps(files, indent=2, sort_keys=True)+'\n')
    delete_patterns = []
    audit = args.folder / 'audit.json'
    if args.type == 'dataset' and audit.exists():
        for row in json.loads(audit.read_text()).get('excluded', []):
            for kind, suffix in [('labels','.txt'),('drawings','.png'),('images','.jpg')]:
                delete_patterns.append(kind + '/' + row['split'] + '/' + row['case'] + suffix)
    result = api.upload_folder(repo_id=repo, repo_type=args.type, folder_path=args.folder,
                               commit_message='Private owner-review release', ignore_patterns=['.cache/**','**/__pycache__/**'],
                               delete_patterns=delete_patterns or None)
    revision = result.oid
    remote_files = set(api.list_repo_files(repo, repo_type=args.type, revision=revision))
    expected_files = set(files) | {'SHA256SUMS.json'}
    if remote_files - expected_files - {'.gitattributes'}:
        raise RuntimeError('Unexpected remote files; release verification refused')
    verify = args.verify_root / args.name
    snapshot_download(repo_id=repo, repo_type=args.type, revision=revision, local_dir=verify,
                      force_download=True, max_workers=8)
    for relative, expected in files.items():
        if digest(verify / relative) != expected:
            raise RuntimeError('Downloaded file hash mismatch: ' + relative)
    if digest(verify / 'SHA256SUMS.json') != digest(args.folder / 'SHA256SUMS.json'):
        raise RuntimeError('Checksum manifest mismatch')
    info = api.repo_info(repo, repo_type=args.type)
    if not info.private: raise RuntimeError('Final privacy check failed')
    report = {'repo':repo, 'type':args.type, 'private':True, 'revision':revision,
              'verified_files':len(files)+1, 'sha256_mismatches':0}
    (args.verify_root / (args.name + '-verification.json')).write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))

if __name__ == '__main__':
    # Credential-bearing exception messages are not printed.
    try:
        main()
    except Exception as exc:
        print('Release operation failed:', type(exc).__name__)
        raise SystemExit(1)
