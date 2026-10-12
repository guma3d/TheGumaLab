"""Audit every final-video cut, preserving final-audio hashes and timings."""
import argparse
import hashlib
import json
from pathlib import Path
from prosody_review import acoustic_words, energy_activity, calibrate, evaluate, syllables
from sentence_pacing import sentence_units, calibrate_sentences, evaluate_sentence


def run(root):
    from faster_whisper import WhisperModel
    manifest=json.loads((root/'manifest.json').read_text())
    timeline=json.loads((root/'timeline.json').read_text())
    timings={p['index']:p for p in timeline['paragraphs']}
    words_dir=root/'aligned-final';words_dir.mkdir(exist_ok=True)
    model=WhisperModel('turbo',device='cpu',compute_type='int8',cpu_threads=4,
        download_root='/models/whisper',local_files_only=True)
    measured=[]
    for cut in manifest:
        audio=root/f"final-cuts/{cut['index']:03}.wav"
        digest=hashlib.sha256(audio.read_bytes()).hexdigest()
        path=words_dir/f"{cut['index']:03}.json"
        if path.exists() and json.loads(path.read_text())['stage_audio_sha256']==digest:
            row=json.loads(path.read_text())
        else:
            segments,_=model.transcribe(str(audio),language='ko',beam_size=8,
                vad_filter=True,condition_on_previous_text=False,word_timestamps=True)
            segments=list(segments)
            row=dict(index=cut['index'],job_id=cut['tts_job_id'],
                audio_sha256=cut['audio_sha256'],stage_audio_sha256=digest,
                expected=cut['text'],transcript=' '.join(s.text.strip() for s in segments),
                words=[dict(text=w.word.strip(),start=w.start,end=w.end,
                    probability=w.probability,syllables=syllables(w.word))
                    for s in segments for w in (s.words or [])],human_listening_completed=False)
            path.write_text(json.dumps(row,ensure_ascii=False,indent=2))
        activity,_,_=energy_activity(audio)
        result=acoustic_words(row,audio)
        result['sentences']=sentence_units(cut['text'],result['words'],activity)
        result['timeline_start']=timings[cut['index']]['start']
        measured.append(result)
        print(json.dumps(dict(aligned=cut['index'],sentences=len(result['sentences']))),flush=True)
    # Include inter-cut spacing when calculating sentence lead-in pauses.
    previous_end=None
    full_audio=root/'final-voice.wav'
    source=json.loads((root/'source-video.json').read_text())
    assert hashlib.sha256(full_audio.read_bytes()).hexdigest()==source['final_voice_sha256']
    full_activity,_,_=energy_activity(full_audio)
    for row in measured:
        for unit in row['sentences']:
            if unit['status']!='aligned':
                previous_end=None
                continue
            unit['global_start']=row['timeline_start']+unit['start']
            unit['global_end']=row['timeline_start']+unit['end']
            gap=max(0,unit['global_start']-previous_end) if previous_end is not None else 0
            # Word-alignment gaps can contain speech. Confirm a pause using
            # the entire decoded final track, not timestamps alone.
            run_length=longest=0
            if previous_end is not None:
                for value in full_activity[round(previous_end*100):round(unit['global_start']*100)]:
                    run_length=0 if value else run_length+1
                    longest=max(longest,run_length)
            unit['preceding_gap_seconds']=round(gap,3)
            unit['preceding_pause_seconds']=round(longest*.01,3)
            unit['flow_seconds_per_syllable']=(unit['elapsed_seconds']+gap)/unit['syllables']
            previous_end=unit['global_end']
    sentence_calibration=calibrate_sentences(measured)
    word_calibration=calibrate(measured,{6,10})
    word_reviews=[evaluate(row,word_calibration) for row in measured]
    sentences=[]
    for row,word_review in zip(measured,word_reviews):
        for unit in row['sentences']:
            review=evaluate_sentence(unit,sentence_calibration)
            review['index']=row['index']
            review['stage_audio_sha256']=row['stage_audio_sha256']
            if unit['status']=='aligned':
                for finding in word_review['findings']:
                    if finding['type']=='long_pause_candidate':continue # Sentence pause features account for these.
                    span=finding.get('slow',finding)
                    if span.get('end',-1)>unit['start'] and span.get('start',9999)<unit['end']:
                        review['findings'].append(finding)
                review['detected']=bool(review['findings'])
            sentences.append(review)
    detected=[s for s in sentences if s['detected']]
    types=sorted({f['type'] for s in detected for f in s['findings']})
    summary=dict(video_seconds=timeline['duration'],cuts_analyzed=len(measured),
        sentences_total=len(sentences),sentences_aligned=sum(s['status']=='aligned' for s in sentences),
        alignment_review_required=sum(s['status']!='aligned' for s in sentences),
        detected_sentences=len(detected),detected_cuts=len({s['index'] for s in detected}),
        finding_events=sum(len(s['findings']) for s in detected),
        sentences_per_finding={t:sum(any(f['type']==t for f in s['findings']) for s in detected) for t in types},
        human_listening_completed=False,naturalness_passed=False)
    report=dict(revision='sentence-rhythm-screen-v2',source=source,
        sentence_calibration=sentence_calibration,word_calibration=word_calibration,
        summary=summary,measurements=measured,sentences=sentences,word_reviews=word_reviews,
        limitations=['Final decoded audio analyzed; ASR boundaries approximate',
                    'Baseline is provisional, not human-approved normal speech',
                    'Sentence count is unique; categories can overlap',
                    'No detection is not a naturalness pass'])
    (root/'sentence-prosody-review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print(json.dumps(summary,ensure_ascii=False),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('root',type=Path)
    run(parser.parse_args().root)
