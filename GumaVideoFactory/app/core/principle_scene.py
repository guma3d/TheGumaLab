"""Trusted abstract 3D assets. Deliberately not a product/internal reconstruction."""
import math
import sys
from pathlib import Path
import bpy

kind,output=sys.argv[sys.argv.index('--')+1:]
if kind not in ('signal','optics','audio'):raise ValueError('Unsupported principle')
bpy.ops.wm.read_factory_settings(use_empty=True)

def material(name,color,metal=.4):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1)
    p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=.22
    return m

cyan=material('Principle teal',(.02,.65,.7));gold=material('Principle warm',(.95,.4,.08));dark=material('Concept silver',(.3,.36,.4),.8)
def sphere(x,y,z,r,mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,radius=r,location=(x,y,z))
    obj=bpy.context.object;obj.name='PRINCIPLE_ONLY';obj.data.materials.append(mat)
    for p in obj.data.polygons:p.use_smooth=True

if kind=='audio':
    for row in range(3):
        for j in range(55):
            x=-1.4+j/54*2.8;z=(row-1)*.8+math.sin(j*.35)*(.2 if row==1 else .32)
            sphere(x,(row-1)*.24,z,.026,cyan if row==1 else gold)
elif kind=='signal':
    sphere(0,0,0,.22,gold)
    for j in range(8):
        a=j*math.tau/8;x=math.cos(a)*1.15;z=math.sin(a)*1.15
        sphere(x,0,z,.12,cyan)
        for k in range(1,9):sphere(x*k/10,.06*math.sin(k),z*k/10,.025,cyan)
else:
    for j in range(3):
        bpy.ops.mesh.primitive_torus_add(major_radius=.6-j*.09,minor_radius=.045,location=(0,(j-1)*.5,0),rotation=(math.pi/2,0,0))
        bpy.context.object.data.materials.append(dark)
    for j in range(60):
        t=j/59;x=(1-t)*.9; y=-1.4+t*2.8
        sphere(x,y,0,.025,cyan);sphere(-x,y,0,.025,gold)
bpy.ops.wm.save_as_mainfile(filepath=str(Path(output).resolve()))
