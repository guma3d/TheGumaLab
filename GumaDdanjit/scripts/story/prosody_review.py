"""Word-timing screening; flags are review candidates, never human listening."""
import argparse
import hashlib
import json
import re
import statistics
from pathlib import Path


def syllables(text):
    return len(re.findall(r'[가-힣]', text))


def count_is_reliable(word):
    # ASR's "2026년" has many spoken syllables but only one Hangul character.
    # Do not manufacture a slow-word finding from that written representation.
    return word['syllables'] > 0 and not re.search(r'[0-9a-zA-Z%‰]', word['text'])


def extract(manifest, service_root, output):
    from faster_whisper import WhisperModel
    model = WhisperModel('turbo', device='cpu', compute_type='int8', cpu_threads=4,
                         download_root='/models/whisper', local_files_only=True)
    output.mkdir(parents=True, exist_ok=True)
    for cut in manifest:
        path = service_root / cut['tts_job_id'] / 'audio.mp3'
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        assert digest == cut['audio_sha256'], 'Selected source hash mismatch'
        dest = output / f"{cut['index']:03}.json"
        if dest.exists() and json.loads(dest.read_text())['audio_sha256'] == digest:
            continue
        segments, _ = model.transcribe(str(path), language='ko', beam_size=8,
            vad_filter=True, condition_on_previous_text=False, word_timestamps=True)
        segments = list(segments)
        words = [dict(text=w.word.strip(), start=w.start, end=w.end,
                      probability=w.probability, syllables=syllables(w.word))
                 for segment in segments for w in (segment.words or [])]
        result = dict(index=cut['index'], job_id=cut['tts_job_id'],
            audio_sha256=digest, expected=cut['text'],
            transcript=' '.join(s.text.strip() for s in segments), words=words,
            timing_method='faster-whisper turbo word alignment, approximate',
            human_listening_completed=False)
        dest.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps(dict(aligned=cut['index'], words=len(words))), flush=True)


def acoustic_words(row, audio, relative_drop_db=35):
    import numpy as np
    import soundfile as sf
    x, sr = sf.read(audio)
    if x.ndim > 1:
        x = x.mean(axis=1)
    hop = round(sr * .01)
    rms = np.array([np.sqrt(np.mean(x[i:i+hop] ** 2)) for i in range(0, len(x), hop)])
    db = 20 * np.log10(rms + 1e-10)
    threshold = max(-48, float(db.max()) - relative_drop_db)
    active = db > threshold
    # Energy activity is a proxy, not phonetic forced alignment. Keep its
    # threshold and sensitivity explicit, and do not label pauses as vowels.
    def longest_quiet(values):
        best = current = 0
        for value in values:
            current = 0 if value else current + 1
            best = max(best, current)
        return round(best * .01, 3)
    result = dict(row, words=[])
    for word in row['words']:
        a, b = round(word['start'] * 100), round(word['end'] * 100)
        samples = active[a:b]
        duration = max(0, word['end'] - word['start'])
        active_time = float(samples.sum()) * .01
        result['words'].append(dict(word, duration=round(duration, 3),
            active_seconds=round(active_time, 3),
            active_seconds_per_syllable=round(active_time / word['syllables'], 4) if word['syllables'] else None,
            longest_quiet_seconds=longest_quiet(samples),
            quiet_seconds=round(len(samples) * .01 - active_time, 3)))
    result['energy_threshold_dbfs'] = round(threshold, 3)
    result['duration_seconds'] = len(x) / sr
    result['pauses'] = []
    # Find actual quiet runs, including quiet contained in an ASR word span.
    start = None
    for i, value in enumerate(list(active) + [True]):
        if not value and start is None:
            start = i
        if value and start is not None:
            if (i - start) * .01 >= .30:
                result['pauses'].append(dict(start=start * .01, end=i * .01,
                    seconds=round((i - start) * .01, 3), internal=start > 0 and i < len(active)))
            start = None
    result['active_seconds'] = round(float(active.sum()) * .01, 3)
    result['active_syllables_per_second'] = (round(sum(w['syllables'] for w in row['words']) / max(.01, result['active_seconds']), 3)
        if all(count_is_reliable(w) for w in row['words']) else None)
    result['cut_rate_unavailable_reason'] = ('Mixed numeral/Latin notation needs spoken-text alignment'
        if result['active_syllables_per_second'] is None else None)
    return result


def calibrate(rows, excluded_indices):
    peers = [row for row in rows if row['index'] not in excluded_indices]
    values = [w['active_seconds_per_syllable'] for row in peers for w in row['words']
              if count_is_reliable(w) and w['probability'] >= .8 and w['active_seconds'] >= .06]
    if len(values) < 30:
        raise ValueError('At least 30 reliable peer words required')
    center = statistics.median(values)
    mad = statistics.median(abs(v-center) for v in values)
    return dict(revision='word-rhythm-screen-v1', baseline_indices=[r['index'] for r in peers],
        excluded_indices=sorted(excluded_indices), baseline_words=len(values),
        median_active_seconds_per_syllable=center, mad=mad,
        long_word_threshold=max(.32, center + 3 * 1.4826 * mad),
        local_ratio_threshold=2.0, minimum_word_active_seconds=.40,
        internal_pause_threshold_seconds=.70,
        status='provisional screening; baseline peers are not human-approved normal samples')


def evaluate(row, calibration):
    words = row['words']
    if not any(count_is_reliable(w) and w['probability'] >= .8 and w['active_seconds'] >= .06 for w in words):
        raise ValueError('No reliable word timing; cannot screen this audio')
    local = statistics.median(w['active_seconds_per_syllable'] for w in words
        if count_is_reliable(w) and w['probability'] >= .8 and w['active_seconds'] >= .06)
    findings = []
    for word in words:
        rate = word['active_seconds_per_syllable']
        if (rate is not None and count_is_reliable(word) and word['probability'] >= .8
                and word['active_seconds'] >= calibration['minimum_word_active_seconds']
                and rate > calibration['long_word_threshold']
                and rate / max(local, .01) > calibration['local_ratio_threshold']):
            findings.append(dict(type='elongated_word_candidate', text=word['text'],
                start=word['start'], end=word['end'], syllables=word['syllables'],
                active_seconds=word['active_seconds'], active_seconds_per_syllable=rate,
                local_ratio=round(rate/local, 3),
                interpretation='Long acoustic activity per syllable; not a confirmed phoneme/vowel diagnosis'))
    for pause in row['pauses']:
        if pause['internal'] and pause['seconds'] > calibration['internal_pause_threshold_seconds']:
            findings.append(dict(type='long_pause_candidate', **pause))
    # Compare overlapping multiword spans within the same cut; include enough
    # syllables to avoid treating every naturally emphasized short word as slow.
    windows = []
    for i in range(len(words)):
        for j in range(i+1, min(len(words), i+5)):
            selected = words[i:j+1]
            if not all(count_is_reliable(w) for w in selected):
                continue
            count = sum(w['syllables'] for w in selected)
            activity = sum(w['active_seconds'] for w in selected)
            if count >= 8 and activity:
                windows.append(dict(start=selected[0]['start'], end=selected[-1]['end'],
                    text=' '.join(w['text'] for w in selected), active_seconds_per_syllable=activity/count))
                break
    if windows:
        slow, fast = max(windows, key=lambda w:w['active_seconds_per_syllable']), min(windows, key=lambda w:w['active_seconds_per_syllable'])
        ratio = slow['active_seconds_per_syllable'] / max(.01, fast['active_seconds_per_syllable'])
        if ratio > 2:
            findings.append(dict(type='within_cut_pace_variation_candidate', ratio=round(ratio,3), slow=slow, fast=fast))
    return dict(index=row['index'], job_id=row['job_id'], audio_sha256=row['audio_sha256'],
        local_median_active_seconds_per_syllable=local,
        active_syllables_per_second=row['active_syllables_per_second'],
        findings=findings, status='needs_review' if findings else 'no_timing_candidate',
        elongation_candidate=any(f['type']=='elongated_word_candidate' for f in findings),
        pause_findings_are_review_only=True,
        naturalness_passed=False, human_listening_completed=False,
        limitations=['ASR word boundaries are approximate', 'Energy activity is not phonetic alignment',
                     'No candidate does not certify naturalness; listening still required'])


def production_summary(root):
    """A missing or stale timing report cannot silently become a quality pass."""
    path = root/'prosody-review.json'
    if not path.exists():
        return dict(status='not_run', naturalness_passed=False, human_listening_completed=False)
    report = json.loads(path.read_text())
    manifest_path = root/'voice-manifest.json'
    manifest = json.loads(manifest_path.read_text())
    release_path = root/'audio-release.json'
    if release_path.exists():
        release = json.loads(release_path.read_text())
        if release.get('voice_manifest_sha256') != hashlib.sha256(manifest_path.read_bytes()).hexdigest():
            raise ValueError('Audio release belongs to another voice manifest')
    cuts = {c['index']:c for c in report['cuts']}
    for voice in manifest:
        cut = cuts.get(voice['index'])
        if not cut or cut['audio_sha256'] != voice['audio_sha256']:
            raise ValueError(f"Missing/stale prosody review for cut {voice['index']}")
    findings = [c for c in cuts.values() if c['index'] in {v['index'] for v in manifest}]
    return dict(status='screened_pending_listening', revision=report['calibration']['revision'],
        checked_cuts=len(manifest), elongation_candidates=[c['index'] for c in findings if c['elongation_candidate']],
        timing_review_candidates=[c['index'] for c in findings if c['findings']],
        report_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        naturalness_passed=False, human_listening_completed=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('manifest', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--service-root', type=Path, default=Path('/app/storage'))
    parser.add_argument('--analyze', action='store_true')
    parser.add_argument('--exclude', type=int, nargs='*', default=[10])
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text())
    if not args.analyze:
        extract(manifest, args.service_root, args.output)
    else:
        rows = [acoustic_words(json.loads((args.output/f"{c['index']:03}.json").read_text()),
                    args.service_root/c['tts_job_id']/'original.wav') for c in manifest]
        calibration = calibrate(rows, set(args.exclude))
        report = dict(calibration=calibration, measurements=rows,
            cuts=[evaluate(row, calibration) for row in rows], human_listening_completed=False)
        path = args.output.parent/'prosody-review.json'
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps(dict(cuts=len(rows), candidates=[r['index'] for r in report['cuts'] if r['findings']],
            held_out=[r for r in report['cuts'] if r['index'] in args.exclude]),ensure_ascii=False),flush=True)
