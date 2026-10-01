"""Rebuild static, allowlisted material nodes without source animation/scripts."""
from pathlib import Path
import bpy

NODE_PROPERTIES = {
    'BSDF_PRINCIPLED': ('distribution', 'subsurface_method'),
    'TEX_IMAGE': ('interpolation', 'projection', 'extension'),
    'UVMAP': ('uv_map',),
    'NORMAL_MAP': ('space', 'uv_map'),
    'SEPARATE_COLOR': ('mode',),
    'VECT_MATH': ('operation',),
    'MATH': ('operation', 'use_clamp'),
    'RGB': (), 'VALUE': (),
}


def rebuild_material(original, asset_path):
    mat = bpy.data.materials.new('Safe product material')
    mat.use_nodes = True
    if original is None:
        return mat
    mat.diffuse_color = original.diffuse_color[:]
    if not original.use_nodes:
        mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value = original.diffuse_color[:]
        return mat
    output = next((n for n in original.node_tree.nodes if n.type == 'OUTPUT_MATERIAL' and n.is_active_output), None)
    if not output or not output.inputs['Surface'].is_linked:
        raise ValueError('제품 재질의 표면 연결을 확인할 수 없습니다.')
    source = output.inputs['Surface'].links[0].from_node
    if source.type != 'BSDF_PRINCIPLED':
        raise ValueError('지원하지 않는 제품 표면 재질입니다. 임의로 대체하지 않습니다.')
    mat.node_tree.nodes.clear()
    copied = {}

    def clone(node):
        if node in copied:
            return copied[node]
        if node.type not in NODE_PROPERTIES:
            raise ValueError('지원하지 않는 제품 재질 노드: ' + node.type)
        target = mat.node_tree.nodes.new(node.bl_idname)
        copied[node] = target
        for attr in NODE_PROPERTIES[node.type]:
            setattr(target, attr, getattr(node, attr))
        if node.type == 'TEX_IMAGE':
            im = node.image
            if not im or im.source not in ('FILE', 'GENERATED'):
                raise ValueError('제품 텍스처를 확인할 수 없습니다.')
            local = Path(bpy.path.abspath(im.filepath)).resolve()
            if not im.packed_file and not local.is_relative_to(asset_path.parent.resolve()):
                raise ValueError('제품 자료 외부의 텍스처는 사용할 수 없습니다.')
            if not 0 < im.size[0] * im.size[1] <= 25000000:
                raise ValueError('제품 텍스처 크기 제한을 초과했습니다.')
            target.image = im.copy()
            target.image.animation_data_clear()
            target.image.pack()
        # Socket identifiers retain duplicate inputs (e.g. Vector Math operands).
        for old, new in zip(node.inputs, target.inputs):
            if hasattr(old, 'default_value') and hasattr(new, 'default_value'):
                value = old.default_value
                new.default_value = value[:] if hasattr(value, '__len__') else value
            if old.is_linked:
                link = old.links[0]
                upstream = clone(link.from_node)
                index = list(link.from_node.outputs).index(link.from_socket)
                mat.node_tree.links.new(upstream.outputs[index], new)
        if node.type in ('RGB', 'VALUE'):
            value = node.outputs[0].default_value
            target.outputs[0].default_value = value[:] if hasattr(value, '__len__') else value
        return target

    bsdf = clone(source)
    end = mat.node_tree.nodes.new('ShaderNodeOutputMaterial')
    mat.node_tree.links.new(bsdf.outputs['BSDF'], end.inputs['Surface'])
    return mat
