"""Render official feature imagery as unmodified textures in a real 3D stage.

This is a reference presentation, never a claim of recovered hidden geometry.
"""
import argparse
import math
import sys
from pathlib import Path
import bpy
from mathutils import Vector


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--image',required=True)
    parser.add_argument('--output',required=True);parser.add_argument('--angle',type=float,default=25)
    parser.add_argument('--kind',choices=('display','thermal'),default='display')
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    # Trusted local Blender helpers only; no downloaded code is evaluated.
    sys.path.insert(0,str(Path(__file__).parent))
    from blender_scene import lighting, material, camera
    bpy.ops.wm.read_factory_settings(use_empty=True)
    if args.kind=='thermal':
        # An abstract phase-change path, deliberately without a component enclosure.
        for index in range(140):
            theta=2*math.pi*index/140
            warm=math.sin(theta)>0
            color=(1,.25,.025) if warm else (.03,.7,1)
            point=(.7*math.sin(theta),.32*math.sin(theta*2),.8*math.cos(theta))
            bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=8,radius=.012 if warm else .022,location=point)
            obj=bpy.context.object;obj.name='Abstract vapor' if warm else 'Abstract condensate'
            obj.data.materials.append(material(obj.name,color,.25,.15))
        for z,color,name in [(-.8,(1,.18,.01),'Evaporation region'),(.8,(.01,.5,1),'Condensation region')]:
            bpy.ops.mesh.primitive_torus_add(major_radius=.18,minor_radius=.025,location=(0,0,z))
            bpy.context.object.name=name;bpy.context.object.data.materials.append(material(name,color,.4,.2))
        lighting();camera(args.angle,distance=4.3,elevation=.5)
        scene=bpy.context.scene;scene.cycles.samples=128
        scene.render.resolution_x=1080;scene.render.resolution_y=1920;scene.render.resolution_percentage=100
        scene.render.image_settings.file_format='PNG'
        bpy.ops.wm.save_as_mainfile(filepath=str(Path(args.output).with_suffix('.blend')))
        scene.render.filepath=args.output;bpy.ops.render.render(write_still=True)
        return
    image=bpy.data.images.load(args.image);image.pack()
    ratio=image.size[0]/image.size[1]
    width=2.4; height=width/ratio
    bpy.ops.mesh.primitive_cube_add(size=1,location=(0,.015,0))
    backing=bpy.context.object;backing.name='OFFICIAL_REFERENCE_DISPLAY'
    backing.dimensions=(width+.06,.08,height+.06)
    backing.data.materials.append(material('Anodized display frame',(.025,.03,.035),.8,.22))
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    bevel=backing.modifiers.new('Precision rounded edge','BEVEL');bevel.width=.025;bevel.segments=5
    mesh=bpy.data.meshes.new('Reference surface')
    mesh.from_pydata([(-width/2,-.031,-height/2),(width/2,-.031,-height/2),(width/2,-.031,height/2),(-width/2,-.031,height/2)],[],[(0,1,2,3)])
    mesh.uv_layers.new(name='UVMap')
    for loop,uv in zip(mesh.uv_layers.active.data,[(0,0),(1,0),(1,1),(0,1)]):loop.uv=uv
    obj=bpy.data.objects.new('Unmodified manufacturer image',mesh);bpy.context.collection.objects.link(obj)
    mat=bpy.data.materials.new('Official image - preserved pixels');mat.use_nodes=True
    nodes=mat.node_tree.nodes;nodes.clear()
    tex=nodes.new('ShaderNodeTexImage');tex.image=image
    emission=nodes.new('ShaderNodeEmission');emission.inputs['Strength'].default_value=.8
    out=nodes.new('ShaderNodeOutputMaterial')
    mat.node_tree.links.new(tex.outputs['Color'],emission.inputs['Color']);mat.node_tree.links.new(emission.outputs[0],out.inputs['Surface'])
    mesh.materials.append(mat)
    lighting();camera(args.angle,distance=5.8,elevation=.5)
    scene=bpy.context.scene;scene.cycles.samples=128
    scene.render.resolution_x=1080;scene.render.resolution_y=1920;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'
    bpy.ops.wm.save_as_mainfile(filepath=str(Path(args.output).with_suffix('.blend')))
    scene.render.filepath=args.output;bpy.ops.render.render(write_still=True)


if __name__=='__main__':main()
