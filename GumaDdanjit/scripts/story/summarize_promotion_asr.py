"""Compare each final take with its text; normalization never silently waives differences."""
import hashlib,json,re,sys
from difflib import SequenceMatcher
from pathlib import Path
from display_captions import REPLACEMENTS
root=Path(sys.argv[1]);rows=json.loads((root/'asr.json').read_text());voices=json.loads((root/'voice-manifest.json').read_text())
assert len(rows)==len(voices)==114
def canonical(s):
    s=re.sub(r'\s','',s)
    for a,b in sorted(REPLACEMENTS.items(),key=lambda x:len(x[0]),reverse=True):s=s.replace(a.replace(' ',''),b.replace(' ',''))
    for a,b in {'2만5천원':'25000원','2만2천원':'22000원','2.5만원':'25000원','2.2만원':'22000원'}.items():s=s.replace(a,b)
    return s.replace('퍼센트','%').lower()
def norm(s):return re.sub(r'[^가-힣a-zA-Z0-9]','',canonical(s))
def numbers(s):return re.findall(r'\d+(?:\.\d+)?',canonical(s).replace(',',''))
notesfile=root/'asr-manual-review.json';notes=json.loads(notesfile.read_text()) if notesfile.exists() else []
issues=[]
for voice in voices:
    row=next(r for r in rows if r['index']==voice['index'])
    assert row['audio_sha256']==voice['audio_sha256'] and row['expected']==voice['text']
    if row.get('processed_sha256'):
        assert hashlib.sha256((root/'processed'/f'{voice["index"]:03}.wav').read_bytes()).hexdigest()==row['processed_sha256']
    expected,actual=norm(row['expected']),norm(row['transcript'])
    expected_numbers,actual_numbers=numbers(row['expected']),numbers(row['transcript'])
    if expected!=actual or expected_numbers!=actual_numbers:
        approved=next((n for n in notes if n['index']==voice['index'] and n['audio_sha256']==row['audio_sha256'] and n['transcript']==row['transcript'] and n.get('verdict') in ('transcription_equivalent','non_speech_asr_artifact')),None)
        assert expected_numbers==actual_numbers or (approved and approved.get('numeric_equivalence_verified')), 'Survey/calculation number mismatch requires repair or explicit verified equivalence'
        issues.append(dict(index=voice['index'],expected=row['expected'],transcript=row['transcript'],audio_sha256=row['audio_sha256'],expected_numbers=expected_numbers,transcribed_numbers=actual_numbers,similarity=SequenceMatcher(None,expected,actual).ratio(),reviewed_equivalent=bool(approved),note=approved.get('note','') if approved else ''))
(root/'asr-differences.json').write_text(json.dumps(issues,ensure_ascii=False,indent=2),encoding='utf-8')
remaining=sum(not i['reviewed_equivalent'] for i in issues)
print(json.dumps({'cuts':len(rows),'differences':len(issues),'unresolved':remaining}),flush=True)
if remaining:raise SystemExit('Inspect unresolved transcript differences before publishing.')
review=json.loads((root/'production-review.json').read_text());review['asr_review']=dict(cut_count=114,meaningful_mismatches=0,normalized_exact_matches=114-len(issues),reviewed_transcription_differences=len(issues),asr_sha256=hashlib.sha256((root/'asr.json').read_bytes()).hexdigest(),human_listening_completed=False)
(root/'production-review.json').write_text(json.dumps(review,ensure_ascii=False,indent=2),encoding='utf-8')
