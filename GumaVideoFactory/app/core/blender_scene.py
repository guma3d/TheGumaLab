"""Trusted Blender entry point. Never execute Python supplied by a model/asset."""
import argparse
import json
import math
import sys
from pathlib import Path
import bpy
import _cycles
from mathutils import Vector


def material(name, color, metallic=.2, roughness=.3):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color[:3], 1)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*color[:3], 1)
    bsdf.inputs['Metallic'].default_value = metallic
    bsdf.inputs['Roughness'].default_value = roughness
    return mat


def build_blueprint(path):
    data = json.loads(path.read_text())
    for part in data['parts']:
        shape = part['shape']
        if shape == 'box': bpy.ops.mesh.primitive_cube_add(size=1)
        elif shape == 'sphere': bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=.5)
        elif shape == 'cylinder': bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=.5, depth=1)
        elif shape == 'torus': bpy.ops.mesh.primitive_torus_add(major_segments=64, minor_segments=16, major_radius=.4, minor_radius=.1)
        else: raise ValueError('Unsupported geometry')
        obj = bpy.context.object
        obj.name = part['name']
        obj.dimensions = part['dimensions']
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        obj.rotation_euler = [math.radians(v) for v in part['rotation_degrees']]
        obj.location = part['position']
        obj.data.materials.append(material(obj.name, part['color'], part['metallic'], part['roughness']))
        if shape in ('box', 'cylinder') and part['bevel']:
            mod = obj.modifiers.new('Edge finish', 'BEVEL')
            mod.width = min(part['bevel'], min(part['dimensions']) * .3); mod.segments = 4
        for polygon in obj.data.polygons: polygon.use_smooth = shape != 'box'


def import_model(path):
    if path.suffix == '.blend':
        with bpy.data.libraries.load(str(path), link=False) as (src, dst):
            dst.objects = src.objects[:1000]
        for obj in dst.objects:
            if obj and obj.type == 'MESH': bpy.context.scene.collection.objects.link(obj)
    elif path.suffix == '.glb': bpy.ops.import_scene.gltf(filepath=str(path))
    elif path.suffix == '.obj': bpy.ops.wm.obj_import(filepath=str(path))
    elif path.suffix == '.fbx': bpy.ops.import_scene.fbx(filepath=str(path))
    elif path.suffix == '.usdz': bpy.ops.wm.usd_import(filepath=str(path))
    else: raise ValueError('지원하지 않는 모델 형식')
    # Only static mesh geometry survives. Never evaluate downloaded drivers,
    # scripts, geometry nodes, external textures or object constraints.
    bpy.context.view_layer.update()
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    if not meshes or sum(len(o.data.vertices) for o in meshes) > 3000000:
        raise ValueError('모델이 비어 있거나 300만 정점 제한을 초과했습니다.')
    def clean_material(original):
        color=tuple(original.diffuse_color[:3]) if original else (.3,.3,.3)
        principled=next((n for n in original.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None) if original and original.use_nodes else None
        if principled: color=tuple(principled.inputs['Base Color'].default_value[:3])
        mat=material('Safe product material',color,
            principled.inputs['Metallic'].default_value if principled else .2,
            max(.05,principled.inputs['Roughness'].default_value) if principled else .3)
        if principled:
            links=principled.inputs['Base Color'].links
            source=links[0].from_node if links else None
            if source and source.type=='TEX_IMAGE' and source.image:
                im=source.image
                local=Path(bpy.path.abspath(im.filepath)).resolve()
                # Rebuild a fresh static material; never copy downloaded nodes,
                # drivers or groups. Preserve packed/asset-local base textures.
                if im.packed_file or local.is_relative_to(path.parent.resolve()):
                    if im.size[0]*im.size[1]<=25000000:
                        image_node=mat.node_tree.nodes.new('ShaderNodeTexImage');image_node.image=im.copy()
                        try:image_node.image.pack()
                        except RuntimeError:pass
                        mat.node_tree.links.new(image_node.outputs['Color'],mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
        return mat
    records = [(o.data.copy(), o.matrix_world.copy(), o.name,
                [clean_material(m) for m in o.data.materials]) for o in meshes]
    for obj in list(bpy.data.objects): bpy.data.objects.remove(obj, do_unlink=True)
    for mesh, matrix, name, materials in records:
        obj = bpy.data.objects.new(name, mesh); bpy.context.collection.objects.link(obj); obj.matrix_world = matrix
        mesh.materials.clear()
        for mat in materials or [material(name,(.3,.3,.3))]: mesh.materials.append(mat)
    for text in list(bpy.data.texts): bpy.data.texts.remove(text)


def normalize():
    bpy.context.view_layer.update()
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    points = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
    low = Vector([min(p[i] for p in points) for i in range(3)])
    high = Vector([max(p[i] for p in points) for i in range(3)])
    scale = 2 / max(high - low)
    center = (low + high) / 2
    root = bpy.data.objects.new('PRODUCT_ROOT', None); bpy.context.collection.objects.link(root)
    for obj in meshes:
        matrix = obj.matrix_world.copy(); obj.parent = root; obj.matrix_world = matrix
    root.location = -center * scale; root.scale = (scale,) * 3
    bpy.context.view_layer.update()


def lighting():
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'; scene.cycles.device = 'CPU'; scene.cycles.use_denoising = bool(getattr(_cycles,'with_openimagedenoise',False))
    scene.world = bpy.data.worlds.new('Studio world'); scene.world.use_nodes = True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value = (.04,.055,.07,1)
    scene.world.node_tree.nodes['Background'].inputs[1].default_value = .35
    for name, loc, energy, size, color in [('Key', (3,-4,5),700,4,(1,.92,.83)), ('Fill',(-4,-1,2),500,3,(.65,.85,1)),('Rim',(1,3,4),900,3,(.6,1,.95))]:
        light = bpy.data.lights.new(name,'AREA'); light.energy=energy; light.shape='DISK'; light.size=size; light.color=color
        obj=bpy.data.objects.new(name,light); scene.collection.objects.link(obj); obj.location=loc
        obj.rotation_euler=(-obj.location).to_track_quat('-Z','Y').to_euler()
    bpy.ops.mesh.primitive_plane_add(size=200, location=(0,0,-1.12))
    bpy.context.object.name='STUDIO_FLOOR'; bpy.context.object.data.materials.append(material('Floor',(.018,.027,.032),.15,.3))
    cam=bpy.data.cameras.new('Studio camera'); obj=bpy.data.objects.new('Studio camera',cam); scene.collection.objects.link(obj); scene.camera=obj; cam.lens=55
    scene.view_settings.view_transform='AgX'


def camera(angle, distance=5.4, elevation=1.25):
    obj=bpy.context.scene.camera
    obj.location=(math.sin(math.radians(angle))*distance, -math.cos(math.radians(angle))*distance, elevation)
    obj.rotation_euler=(-obj.location).to_track_quat('-Z','Y').to_euler()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--build'); parser.add_argument('--source'); parser.add_argument('--scene')
    parser.add_argument('--output', required=True); parser.add_argument('--angle',type=float,default=25)
    parser.add_argument('--width',type=int,default=384); parser.add_argument('--height',type=int,default=684)
    parser.add_argument('--samples',type=int,default=64); parser.add_argument('--frames',type=int,default=1)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:]); output=Path(args.output)
    if args.scene:
        bpy.ops.wm.open_mainfile(filepath=args.scene, load_ui=False, use_scripts=False)
    else:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        if args.build: build_blueprint(Path(args.build))
        else: import_model(Path(args.source))
        normalize(); lighting(); camera(25)
        bpy.ops.wm.save_as_mainfile(filepath=str(output/'model.blend'))
    scene=bpy.context.scene
    scene.cycles.samples=args.samples
    scene.cycles.use_denoising=bool(getattr(_cycles,'with_openimagedenoise',False))
    scene.render.threads_mode='FIXED'; scene.render.threads=4
    scene.render.resolution_x=args.width; scene.render.resolution_y=args.height; scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'; scene.render.fps=24
    if args.scene:
        for frame in range(args.frames):
            camera(args.angle + (frame / max(1,args.frames-1) - .5)*16 if args.frames>1 else args.angle)
            scene.render.filepath=str(output / f'frame_{frame+1:04d}.png') if args.frames>1 else str(output)
            bpy.ops.render.render(write_still=True)
    else:
        for index, angle in enumerate((25,145,225,315),1):
            camera(angle); scene.render.filepath=str(output/f'view_{index}.png'); bpy.ops.render.render(write_still=True)


if __name__=='__main__': main()
