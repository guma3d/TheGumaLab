"""Non-destructive, versioned backup of originals, metadata and consistent SQLite snapshot."""
import hashlib
import json
import sqlite3
import tempfile
import zipfile
from contextlib import closing
from datetime import datetime
from pathlib import Path

root = Path(__file__).resolve().parents[1] / 'storage'
destination = root / 'backups'
destination.mkdir(exist_ok=True)
stamp = datetime.now().strftime('%Y%m%d-%H%M%S-%f')
output = destination / f'GumaStory-{stamp}.zip'
manifest = []
with tempfile.TemporaryDirectory(prefix='gumastory-backup-') as temporary:
    snapshot = Path(temporary) / 'gumastory.sqlite3'
    with closing(sqlite3.connect(root/'gumastory.sqlite3')) as src, closing(sqlite3.connect(snapshot)) as dst:
        src.backup(dst)
    with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_STORED) as archive:
        archive.write(snapshot, 'gumastory.sqlite3')
        for directory in ('assets', 'imports', 'exports', 'verification', 'productions'):
            for file in sorted((root/directory).rglob('*')):
                if not file.is_file():
                    continue
                relative = file.relative_to(root).as_posix()
                archive.write(file, relative)
                with file.open('rb') as content:
                    manifest.append({'file': relative, 'sha256': hashlib.file_digest(content, 'sha256').hexdigest()})
        archive.writestr('backup-manifest.json', json.dumps(manifest, ensure_ascii=False, indent=2))
print(json.dumps({'backup': str(output), 'files':len(manifest), 'bytes':output.stat().st_size}, ensure_ascii=False))
