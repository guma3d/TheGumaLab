"""Codex/Astra operator CLI. Browser outcomes require actual UI inspection."""
import argparse
import json
from app.core import shopping as s, versions as store

parser=argparse.ArgumentParser()
parser.add_argument('command',choices=['build','seal','enqueue','pending','review','claim','private','public'])
parser.add_argument('target',nargs='?')
parser.add_argument('--file')
parser.add_argument('--version',type=int)
parser.add_argument('--regenerate',action='store_true')
a=parser.parse_args()
if a.command=='build':result=s.build(a.target,a.file)
elif a.command=='seal':result=s.seal(a.target,a.version,a.file)
elif a.command=='enqueue':result=s.enqueue(a.target,a.version,a.regenerate)
elif a.command=='pending':
    result=[]
    for path in store.ROOT.glob('*/Video/v*/upload.json'):
        data=s.read(path)
        if data['state'] in ('quality_review','upload_pending','uploading','publish_requested'):
            result.append(dict(idea_id=path.parents[2].name,version=int(path.parent.name[1:]),folder=str(path.parent),**data))
else:result=s.publication(a.target,a.version,a.command,s.read(a.file))
print(json.dumps(result,ensure_ascii=False))
