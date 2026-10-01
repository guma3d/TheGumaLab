"""Run with Blender --background --python; no network or product fixture needed."""
import sys
import tempfile
from pathlib import Path
import bpy
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app' / 'core'))
from blender_materials import rebuild_material

bpy.ops.wm.read_factory_settings(use_empty=True)
source = bpy.data.materials.new('source')
source.use_nodes = True
nodes = source.node_tree.nodes
links = source.node_tree.links
bsdf = nodes.get('Principled BSDF')
uv = nodes.new('ShaderNodeUVMap'); uv.uv_map = 'st1'
texture = nodes.new('ShaderNodeTexImage')
texture.image = bpy.data.images.new('static', width=4, height=4)
texture.image.filepath_raw = tempfile.gettempdir() + '/material-regression.png'
texture.image.file_format = 'PNG'
texture.image.save()
texture.image = bpy.data.images.load(texture.image.filepath_raw)
texture.image.pack()
links.new(uv.outputs['UV'], texture.inputs['Vector'])
links.new(texture.outputs['Color'], bsdf.inputs['Base Color'])
separate = nodes.new('ShaderNodeSeparateColor')
links.new(texture.outputs['Color'], separate.inputs['Color'])
links.new(separate.outputs['Red'], bsdf.inputs['Roughness'])
normal = nodes.new('ShaderNodeNormalMap'); normal.uv_map = 'st1'
links.new(texture.outputs['Color'], normal.inputs['Color'])
links.new(normal.outputs['Normal'], bsdf.inputs['Normal'])
bsdf.inputs['Metallic'].default_value = .7
source.diffuse_color = (.2, .3, .4, 1)
source.driver_add('diffuse_color', 0).driver.expression = '0.9'
clean = rebuild_material(source, Path('/tmp/product.glb'))
assert clean.animation_data is None
assert clean.node_tree.animation_data is None
safe_bsdf = next(n for n in clean.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
safe_texture = safe_bsdf.inputs['Base Color'].links[0].from_node
assert safe_texture.inputs['Vector'].links[0].from_node.uv_map == 'st1'
assert safe_texture.image != texture.image and safe_texture.image.packed_file
assert safe_bsdf.inputs['Roughness'].links[0].from_node.type == 'SEPARATE_COLOR'
assert safe_bsdf.inputs['Normal'].links[0].from_node.uv_map == 'st1'
assert abs(safe_bsdf.inputs['Metallic'].default_value - .7) < 1e-6
# Unsupported upstream graphs fail explicitly instead of losing product details.
unsupported = nodes.new('ShaderNodeTexNoise')
links.new(unsupported.outputs['Color'], bsdf.inputs['Base Color'])
try:
    rebuild_material(source, Path('/tmp/product.glb'))
except ValueError:
    pass
else:
    raise AssertionError('Unsupported graph silently substituted')
print('Static material regression: OK (UV, PBR, textures, no drivers, fail closed)')
