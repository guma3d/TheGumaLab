"""Host-side handoff for inspected quiet takes; never overwrite successful audio."""
import json,shutil,subprocess,sys,time
from pathlib import Path
root=Path(sys.argv[1]).resolve();tts=Path(sys.argv[2]).resolve();queue=root/'voice-queue.json'
data=json.loads(queue.read_text(encoding='utf-8'))
(tts/'promotion-v3-queue-check.json').write_text(json.dumps(data),encoding='utf-8')
result=subprocess.run(['docker','exec','-e','PYTHONPATH=/app','-e','GUMATTS_TOKEN_FILE=/app/storage/service-token','GumaTTS_app','python','/app/storage/promotion-v3-audit/retry_quiet_cuts.py','/app/storage'],capture_output=True,text=True,encoding='utf-8')
if result.returncode:raise RuntimeError(result.stderr)
changes=json.loads((tts/'promotion-v3-quiet-retries.json').read_text(encoding='utf-8'))
if changes:
    shutil.copy2(queue,root/f'voice-queue-before-retry-{time.time_ns()}.json')
    data.update(changes);queue.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
print(result.stdout.strip())
