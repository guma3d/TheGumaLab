"""Recheck a flagged transcript on the exact edge-trimmed audio used by the film."""
import hashlib,json,sys
from pathlib import Path
from faster_whisper import WhisperModel
root=Path(sys.argv[1]);use_vad='--no-vad' not in sys.argv[2:];indices=[int(n) for n in sys.argv[2:] if n!='--no-vad']
rows=json.loads((root/'asr.json').read_text())
model=WhisperModel('turbo',device='cpu',compute_type='int8',cpu_threads=4,download_root='/models/whisper',local_files_only=True)
for index in indices:
    row=next(r for r in rows if r['index']==index);path=root/'processed'/f'{index:03}.wav'
    segments,_=model.transcribe(str(path),language='ko',beam_size=8,vad_filter=use_vad,word_timestamps=True,condition_on_previous_text=False)
    segments=list(segments)
    row.update(raw_transcript=row['transcript'],raw_segments=row['segments'],transcript=' '.join(s.text.strip() for s in segments),segments=[dict(start=s.start,end=s.end,text=s.text) for s in segments],transcription_source='exact edge-trimmed film cut',asr_settings=dict(beam_size=8,vad_filter=use_vad,condition_on_previous_text=False),processed_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    print(json.dumps({'index':index,'transcript':row['transcript']},ensure_ascii=False),flush=True)
(root/'asr.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
