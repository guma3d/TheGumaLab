"""Codex/Astra operator CLI. Browser outcomes require actual UI inspection."""
import argparse
import json
from app.core import shopping as s, versions as store

parser=argparse.ArgumentParser()
parser.add_argument('command',choices=['build','seal','enqueue','pending','review','review_web','review_private','authorize_upload','claim','private','public','edits','edit-done'])
parser.add_argument('target',nargs='?')
parser.add_argument('--file')
parser.add_argument('--version',type=int)
parser.add_argument('--regenerate',action='store_true')
a=parser.parse_args()
if a.command=='build':result=s.build(a.target,a.file)
elif a.command=='seal':result=s.seal(a.target,a.version,a.file)
elif a.command=='enqueue':result=s.enqueue(a.target,a.version,a.regenerate)
elif a.command=='edits':
    result=[s.read(p) for p in store.ROOT.glob('*/edit_requests/*.json') if s.read(p).get('state')=='pending']
elif a.command=='edit-done':
    v=store.get(a.target,'Video',a.version)
    if v.get('publication_state') not in ('web_review','private','public'):raise ValueError('수정 영상의 웹 검토본 저장을 먼저 확인하세요.')
    path=store.directory(a.target)/'edit_requests'/(a.file+'.json')
    if path.parent.resolve()!=(store.directory(a.target)/'edit_requests').resolve():raise ValueError('잘못된 요청 ID')
    result=s.read(path);result.update(state='completed',result_video_version=a.version,completed_at=s.now_kst().isoformat());store.write_json(path,result)
elif a.command=='pending':
    result=[]
    for path in store.ROOT.glob('*/Video/v*/upload.json'):
        data=s.read(path)
        if data['state'] in ('upload_requested','uploading','publish_requested'):
            result.append(dict(idea_id=path.parents[2].name,version=int(path.parent.name[1:]),folder=str(path.parent),**data))
else:result=s.publication(a.target,a.version,a.command,s.read(a.file))
print(json.dumps(result,ensure_ascii=False))
