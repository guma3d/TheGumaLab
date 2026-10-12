"""Normalize sentence timing by immutable spoken syllables, not printed digits."""
import re
import statistics
from difflib import SequenceMatcher
from display_captions import display_text
from prosody_review import syllables


def canonical(text):
    return re.sub(r'[^가-힣a-z0-9%]', '', display_text(text).lower())


def matched_word_indices(units):
    return sorted({i for s in units if s['status']=='aligned' for i in s['word_indices']})


def sentence_units(expected, words, active):
    texts = [p.strip() for p in re.findall(r'[^.!?。！？]+[.!?。！？]*', expected) if p.strip()]
    actual = ''.join(canonical(w['text']) for w in words)
    owners = [i for i,w in enumerate(words) for _ in canonical(w['text'])]
    target = ''.join(canonical(t) for t in texts)
    mapping = {}
    for block in SequenceMatcher(None, target, actual, autojunk=False).get_matching_blocks():
        for offset in range(block.size):
            mapping[block.a+offset] = block.b+offset
    units, cursor, previous_end = [], 0, None
    for number,text in enumerate(texts,1):
        normalized = canonical(text)
        matches = [mapping[p] for p in range(cursor,cursor+len(normalized)) if p in mapping]
        cursor += len(normalized)
        coverage = len(matches)/max(1,len(normalized))
        if coverage < .90 or not matches or re.search('[A-Za-z0-9]',text):
            units.append(dict(sentence=number,text=text,status='alignment_review_required',coverage=coverage))
            previous_end=None
            continue
        chosen = sorted(set(owners[p] for p in matches))
        start, end = words[chosen[0]]['start'], words[chosen[-1]]['end']
        a,b = max(0,round(start*100)), min(len(active),round(end*100))
        positions = [i for i in range(a,b) if active[i]]
        if not positions:
            raise ValueError('Sentence alignment contains no acoustic activity')
        # Exclude edge silence from sentence body; retain the preceding pause
        # as its own feature so a long lead-in cannot disappear in trimming.
        a,b = positions[0],positions[-1]+1
        start,end = a*.01,b*.01
        count = syllables(text)
        activity = sum(bool(v) for v in active[a:b])*.01
        elapsed = end-start
        leading = max(0,start-previous_end) if previous_end is not None else 0
        quiet = elapsed-activity
        units.append(dict(sentence=number,text=text,status='aligned',coverage=round(coverage,4),
            syllables=count,start=round(start,3),end=round(end,3),word_indices=chosen,
            active_seconds=round(activity,3),elapsed_seconds=round(elapsed,3),
            quiet_seconds=round(quiet,3),pause_fraction=round(quiet/max(elapsed,.01),4),
            preceding_pause_seconds=round(leading,3),
            active_seconds_per_syllable=activity/count,
            elapsed_seconds_per_syllable=elapsed/count,
            flow_seconds_per_syllable=(elapsed+leading)/count))
        previous_end = end
    return units


def calibrate_sentences(rows, excluded_cuts=(6,10)):
    peers = [s for r in rows if r['index'] not in excluded_cuts for s in r['sentences']
             if s['status']=='aligned' and s['syllables']>=8]
    if len(peers)<15:
        raise ValueError('At least 15 aligned peer sentences required')
    result = dict(revision='sentence-rhythm-screen-v2',baseline_sentences=len(peers),
        excluded_cuts=list(excluded_cuts),minimum_syllables=8,
        pause_fraction_threshold=.25,minimum_quiet_seconds=.60,
        long_pause_seconds=.70, naturalness_passed=False,
        note='Within-video provisional baseline, not human-approved normal speech')
    for key,multiplier in [('active',1.30),('elapsed',1.35)]:
        values=[s[key+'_seconds_per_syllable'] for s in peers]
        center=statistics.median(values)
        mad=statistics.median(abs(v-center) for v in values)
        result[key+'_median']=center
        result[key+'_mad']=mad
        result[key+'_threshold']=max(center*multiplier,center+2*1.4826*mad)
    return result


def evaluate_sentence(sentence, calibration):
    if sentence['status']!='aligned':
        return dict(sentence,findings=[],detected=False,naturalness_passed=False)
    findings=[]
    if sentence['syllables']>=calibration['minimum_syllables']:
        for feature in ('active','elapsed'):
            value=sentence[feature+'_seconds_per_syllable']
            if value>calibration[feature+'_threshold']:
                findings.append(dict(type='slow_sentence_'+feature,
                    value=value,threshold=calibration[feature+'_threshold'],
                    baseline_ratio=value/calibration[feature+'_median']))
        if (sentence['pause_fraction']>calibration['pause_fraction_threshold']
                and sentence['quiet_seconds']>=calibration['minimum_quiet_seconds']):
            findings.append(dict(type='high_sentence_pause_fraction',
                value=sentence['pause_fraction'],quiet_seconds=sentence['quiet_seconds']))
    if sentence['preceding_pause_seconds']>calibration['long_pause_seconds']:
        findings.append(dict(type='long_preceding_sentence_pause',seconds=sentence['preceding_pause_seconds']))
    return dict(sentence,findings=findings,detected=bool(findings),
        naturalness_passed=False,human_listening_completed=False)
