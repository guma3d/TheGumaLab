"""Opt-in integration check: real .blend, multiple views, saved-scene animation."""
from pathlib import Path
import json
from PIL import Image
from app.core.blender_runner import run_blender

folder=Path('/app/storage/verification/blender-smoke');folder.mkdir(parents=True,exist_ok=True)
blueprint=dict(parts=[dict(name='Test enclosure',shape='box',dimensions=[1,0.3,2],position=[0,0,1],rotation_degrees=[0,0,0],color=[.12,.3,.35],metallic=.5,roughness=.25,bevel=.08),dict(name='Test lens',shape='cylinder',dimensions=[.25,.25,.08],position=[.2,-.19,1.6],rotation_degrees=[90,0,0],color=[.03,.03,.04],metallic=.5,roughness=.1,bevel=.01)])
(folder/'blueprint.json').write_text(json.dumps(blueprint))
run_blender(folder,'--build',folder/'blueprint.json','--output',folder,'--width',144,'--height',256,'--samples',4)
assert (folder/'model.blend').stat().st_size>1000
for i in range(1,5):
    with Image.open(folder/f'view_{i}.png') as im:assert im.size==(144,256)
frames=folder/'frames';frames.mkdir(exist_ok=True)
run_blender(folder,'--scene',folder/'model.blend','--output',frames,'--width',144,'--height',256,'--samples',4,'--frames',3)
assert len(list(frames.glob('frame_*.png')))==3
print('PASS: real Blender model, 4 views and 3 animation frames')
