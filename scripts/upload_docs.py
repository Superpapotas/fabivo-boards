"""Update documentation only in three EXISTING HF repositories.

Public targets require --allow-public. Repository visibility is unchanged.

Uses the normal HF credential client without reading or replacing credentials.
Never uploads weights, labels, dataset images or changes repository visibility.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
from huggingface_hub import HfApi, CommitOperationAdd, CommitOperationDelete, hf_hub_download

TARGETS = [
    ('image', 'Superpapotas1/fabivo-boards-image-lora', 'model'),
    ('vlm', 'Superpapotas1/fabivo-boards-vlm-9b', 'model'),
    ('dataset', 'Superpapotas1/fabivo-furniture-boards', 'dataset'),
]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def identity(info):
    return {s.rfilename: (s.blob_id, s.lfs.sha256 if s.lfs else None, s.size) for s in info.siblings}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('root', type=Path)
    ap.add_argument('stage', type=Path)
    ap.add_argument('--allow-public', action='store_true', help='Allow already-public targets; never changes visibility')
    args = ap.parse_args()
    root, stage = args.root.resolve(), args.stage.resolve()
    api = HfApi()
    reports = []
    for family, repo, kind in TARGETS:
        before = api.repo_info(repo, repo_type=kind, files_metadata=True)
        if not before.private and not args.allow_public:
            raise RuntimeError('Public target requires explicit --allow-public')
        baseline = identity(before)
        payload = stage/family/'payload'
        payload.mkdir(parents=True, exist_ok=True)
        card = (root/'hf'/family/'README.md').read_text().replace('../../', '')
        (payload/'README.md').write_text(card)
        files = [payload/'README.md']
        for folder, pattern in [('assets/figures','*'), ('assets/comparisons','*.png'), ('docs','*.md'), ('docs','*.html'), ('results','*.json')]:
            for source in sorted((root/folder).glob(pattern)):
                if not source.is_file():
                    continue
                assert source.suffix in ['.svg','.png','.md','.html','.json']
                destination = payload/source.relative_to(root)
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, destination)
                files.append(destination)
        verify = stage/family/'downloaded'
        manifest_local = Path(hf_hub_download(repo, 'SHA256SUMS.json', repo_type=kind,
                                             revision=before.sha, local_dir=verify))
        manifest = json.loads(manifest_local.read_text())
        removed = {f'assets/figures/m11-gallery-{n}.{ext}' for n in range(1,5) for ext in ['png','svg']} & set(baseline)
        for name in removed:
            manifest.pop(name, None)
        for file in files:
            manifest[str(file.relative_to(payload))] = sha(file)
        (payload/'SHA256SUMS.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
        files.append(payload/'SHA256SUMS.json')
        changes = {str(p.relative_to(payload)) for p in files}
        assert all(p == 'README.md' or p == 'SHA256SUMS.json' or p.startswith(('docs/','results/','assets/figures/','assets/comparisons/')) for p in changes)
        assert not any(p.endswith(('.safetensors','.jpg','.txt')) for p in changes)
        operations = [CommitOperationAdd(path_in_repo=str(p.relative_to(payload)), path_or_fileobj=p) for p in files]
        operations.extend(CommitOperationDelete(path_in_repo=p) for p in sorted(removed))
        result = api.create_commit(repo, repo_type=kind, operations=operations,
                                   parent_commit=before.sha,
                                   commit_message='Explain photo-to-CAD research with actual Fabivo renders and labeled reference composites')
        after = api.repo_info(repo, repo_type=kind, files_metadata=True)
        if after.private != before.private:
            raise RuntimeError('Unexpected repository visibility change')
        current = identity(after)
        if current.get('.gitattributes') != baseline.get('.gitattributes'):
            previous = Path(hf_hub_download(repo, '.gitattributes', repo_type=kind, revision=before.sha)).read_text().splitlines()
            updated = Path(hf_hub_download(repo, '.gitattributes', repo_type=kind, revision=after.sha)).read_text().splitlines()
            expected = {p + ' filter=lfs diff=lfs merge=lfs -text' for p in changes if p.endswith('.png')}
            assert set(previous) <= set(updated), 'Hub removed previous LFS attributes'
            assert set(updated)-set(previous) <= expected, 'Unexpected Hub-managed LFS attribute'
            changes.add('.gitattributes')
        assert all(current[p] == ident for p, ident in baseline.items() if p not in changes and p not in removed), 'Non-documentation file changed'
        assert set(current) == (set(baseline)-removed) | changes, 'Unexpected remote file change'
        for local in files:
            rel = str(local.relative_to(payload))
            downloaded = Path(hf_hub_download(repo, rel, repo_type=kind, revision=result.oid,
                                               local_dir=verify, force_download=True))
            assert sha(local) == sha(downloaded), 'Published byte mismatch'
        reports.append({'repo':repo, 'type':kind, 'private':after.private, 'revision':result.oid,
                        'verified_document_files':len(files), 'preserved_existing_files':len(set(baseline)-changes-removed), 'removed_obsolete_gallery_files':len(removed),
                        'byte_mismatches':0})
        print(repo + ': documentation verified; visibility unchanged; existing non-documentation files unchanged')
        (stage/'verification.json').write_text(json.dumps(reports,indent=2)+'\n')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        # Avoid credential-bearing HTTP exception messages.
        print('Documentation upload failed:', type(exc).__name__)
        raise SystemExit(1)
