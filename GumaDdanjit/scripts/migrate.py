"""Copy, never delete. Use --verify after stopping source writers for final cutover."""
import argparse
import hashlib
import json
import shutil
import sqlite3
from pathlib import Path
from datetime import datetime, timezone

base=Path(__file__).resolve().parents[2]
target=base/'GumaDdanjit/storage'
mapping={'GumaVideoFactory':'shorts','GumaStory':'story','GumaShop':'shop'}

def digest(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def database_content(path):
    with sqlite3.connect(path) as db:
        assert db.execute('pragma integrity_check').fetchone()[0]=='ok'
        tables=[r[0] for r in db.execute("select name from sqlite_master where type='table' and name not like 'sqlite_%' order by name")]
        return {t:sorted(db.execute('select * from "'+t.replace('"','""')+'"').fetchall(),key=repr) for t in tables}

def migrate(verify=False):
    report={'at':datetime.now(timezone.utc).isoformat(),'verified':verify,'modules':{}}
    for source_name,section in mapping.items():
        source=base/source_name/'storage';dest=target/section;dest.mkdir(parents=True,exist_ok=True)
        files=[p for p in source.rglob('*') if p.is_file() and not p.name.endswith(('-wal','-shm')) and '__pycache__' not in p.parts]
        count=0;total=0;hashes=[]
        for src in files:
            out=dest/src.relative_to(source);out.parent.mkdir(parents=True,exist_ok=True)
            if src.suffix=='.sqlite3':
                with sqlite3.connect(src) as a,sqlite3.connect(out) as b:a.backup(b)
                if verify:assert database_content(src)==database_content(out),str(src)
            else:
                if not out.exists() or src.stat().st_size!=out.stat().st_size or src.stat().st_mtime_ns!=out.stat().st_mtime_ns:shutil.copy2(src,out)
                if verify:
                    sha=digest(src)
                    assert sha==digest(out),str(src)
                    hashes.append({'path':src.relative_to(source).as_posix(),'sha256':sha})
            count+=1;total+=src.stat().st_size
        report['modules'][section]={'files':count,'bytes':total,'sha256':hashes}
        print(section,count,round(total/1024**3,2),'GiB',flush=True)
    folder=base/'GumaDdanjit/backups';folder.mkdir(exist_ok=True)
    path=folder/('migration-verified.json' if verify else 'migration-copy.json')
    path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Migration evidence:',path,flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--verify',action='store_true')
    migrate(parser.parse_args().verify)
