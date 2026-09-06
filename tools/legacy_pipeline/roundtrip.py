"""Independent ufbx process readback; compare topology, bindings and evaluated skin."""
from pathlib import Path
import subprocess

from . import math3d as m
from .neutral import evaluate, load, save, validate


def validate_fbx(asset, fbx_path, reader, workdir, clip_name=None,
                 position_tolerance_cm=.001, angle_tolerance_degrees=.01):
    stats=validate(asset); bones=asset['skeleton']['bones']; names=[b['name'] for b in bones]
    reader=Path(reader).resolve(); fbx_path=Path(fbx_path).resolve(); workdir=Path(workdir).resolve()
    if not reader.is_file() or not fbx_path.is_file(): raise ValueError('Reader or FBX file not found')
    workdir.mkdir(parents=True,exist_ok=True)
    output=workdir/'readback.json'; command=[str(reader),str(fbx_path),str(output)]
    clip=next((c for c in asset['animations'] if c['name']==clip_name),None)
    if clip_name and clip is None: raise ValueError('Unknown clip')
    times=[]
    if clip:
        keys=sorted({s['time_seconds'] for t in clip['tracks'] for s in t['samples']})
        times=sorted(set(keys+[(a+b)/2 for a,b in zip(keys,keys[1:])]))
        time_file=workdir/'times.txt';time_file.write_text('\n'.join(format(t,'.17g') for t in times)+'\n',encoding='ascii');command.append(str(time_file))
    subprocess.run(command,check=True,capture_output=True,timeout=120)
    result=load(output); base={n['name']:n for n in result['nodes'] if n['bone']}
    if set(base)!=set(names) or result['bone_count']!=len(names): raise ValueError('Bone set changed')
    for i,b in enumerate(bones):
        if base[b['name']]['parent']!=(names[b['parent']] if b['parent']>=0 else None): raise ValueError('Hierarchy changed')
        if base[b['name']]['has_adjust_transform']: raise ValueError('Reader introduced transform adjustment')
    metrics={'positions_cm':0.,'normals':0.,'uv':0.,'weights':0.,'inverse_bind':0.,'bind_vertex_cm':0.,
             'local_translation_cm':0.,'local_rotation_degrees':0.,'component_origin_cm':0.,'component_matrix':0.,'skinned_vertex_cm':0.,'duration_seconds':0.}
    actual_meshes={x['name']:x for x in result['meshes']}
    if set(actual_meshes)!={x['id'] for x in asset['meshes']}: raise ValueError('Mesh set changed')
    for mesh in asset['meshes']:
        actual=actual_meshes[mesh['id']]
        indices=[i for f in mesh['triangles'] for i in f]
        if actual['indices']!=indices or actual['num_vertices']!=len(mesh['positions']) or actual['num_triangles']!=len(mesh['triangles']): raise ValueError('Topology changed')
        for p,q in zip(mesh['positions'],actual['positions']): metrics['positions_cm']=max(metrics['positions_cm'],m.distance(p,q))
        for corner,vi in enumerate(indices):
            metrics['normals']=max(metrics['normals'],m.distance(mesh['normals'][vi],actual['normals_by_corner'][corner]))
            metrics['uv']=max(metrics['uv'],m.distance(mesh['uv0'][vi],actual['uvs_by_corner'][corner]))
        if actual['materials']!=[x['id'] for x in asset['materials']]: raise ValueError('Material references changed')
        expected_faces=[actual['materials'].index(x) for x in mesh['face_materials']]
        if actual['face_material']!=expected_faces: raise ValueError('Material groups changed')
        weights={}; imported_bones=[dict(b) for b in bones]
        for cluster in actual['clusters']:
            if cluster['bone'] not in names: raise ValueError('Unexpected skin binding')
            bi=names.index(cluster['bone']); ib=cluster['inverse_bind'];imported_bones[bi]={**bones[bi],'inverse_bind':ib}
            metrics['inverse_bind']=max(metrics['inverse_bind'],m.matrix_error(bones[bi]['inverse_bind'],ib))
            for vi,w in cluster['weights']: weights.setdefault(vi,[]).append({'bone':bi,'weight':w})
        imported={**mesh,'positions':actual['positions'],'skin':[]}
        for vi,ws in enumerate(mesh['skin']):
            expected=sorted(ws,key=lambda w:w['bone']); observed=sorted(weights.get(vi,[]),key=lambda w:w['bone'])
            if [w['bone'] for w in expected]!=[w['bone'] for w in observed]: raise ValueError('Influences changed')
            metrics['weights']=max(metrics['weights'],max(abs(w['weight']-q['weight']) for w,q in zip(expected,observed)))
            imported['skin'].append(observed)
        actual['_imported']=imported;actual['_bones']=imported_bones
        source_world=m.world_matrices(bones,[b['rest'] for b in bones])
        for p,q in zip(m.skin(mesh,bones,source_world),m.skin(imported,imported_bones,[base[n]['world_matrix'] for n in names])):
            metrics['bind_vertex_cm']=max(metrics['bind_vertex_cm'],m.distance(p,q))
    if clip:
        if len(result['animations'])!=1 or result['animations'][0]['name']!=clip_name: raise ValueError('Clip changed')
        animation=result['animations'][0]
        metrics['duration_seconds']=abs(animation['end']-animation['start']-clip['duration_seconds'])
        if len(result['frames'])!=len(times): raise ValueError('Missing evaluated times')
        for t,frame in zip(times,result['frames']):
            if t!=frame['time_seconds']: raise ValueError('Evaluation time changed')
            nodes={n['name']:n for n in frame['nodes'] if n['bone']}
            if set(nodes)!=set(names): raise ValueError('Evaluated bone missing')
            local=evaluate(clip,t,len(bones));world=m.world_matrices(bones,local)
            for i,n in enumerate(names):
                node=nodes[n]
                if node['has_adjust_transform'] or node['parent']!=base[n]['parent']: raise ValueError('Evaluated hierarchy adjusted')
                metrics['local_translation_cm']=max(metrics['local_translation_cm'],m.distance(local[i]['translation'],[r[3] for r in node['local_matrix'][:3]]))
                metrics['local_rotation_degrees']=max(metrics['local_rotation_degrees'],m.quaternion_angle(local[i]['rotation'],node['rotation_xyzw']))
                if max(abs(local[i]['scale_shear'][j]-node['scale'][k]) for k,j in enumerate((0,4,8)))>1e-9: raise ValueError('Signed scale changed')
                metrics['component_origin_cm']=max(metrics['component_origin_cm'],m.distance([r[3] for r in world[i][:3]],[r[3] for r in node['world_matrix'][:3]]))
                metrics['component_matrix']=max(metrics['component_matrix'],m.matrix_error(world[i],node['world_matrix']))
            for mesh in asset['meshes']:
                actual=actual_meshes[mesh['id']]
                for p,q in zip(m.skin(mesh,bones,world),m.skin(actual['_imported'],actual['_bones'],[nodes[n]['world_matrix'] for n in names])):
                    metrics['skinned_vertex_cm']=max(metrics['skinned_vertex_cm'],m.distance(p,q))
    elif result['animations']: raise ValueError('Unexpected animation')
    if result['warnings']: raise ValueError('Independent reader emitted warnings')
    exact=('positions_cm','normals','uv','weights','inverse_bind')
    if any(metrics[k]>1e-12 for k in exact): raise ValueError('Geometry/binding round trip changed: '+str(metrics))
    if max(metrics[k] for k in ('bind_vertex_cm','local_translation_cm','component_origin_cm','skinned_vertex_cm'))>position_tolerance_cm or metrics['local_rotation_degrees']>angle_tolerance_degrees or metrics['duration_seconds']>.001:
        raise ValueError('Round-trip tolerance exceeded: '+str(metrics))
    summary={'status':'PASS_NUMERICAL_SAMPLED','corpus':asset['provenance']['kind'],'statistics':stats,'clip':clip_name,'audit_times':len(times),
             'errors':metrics,'position_tolerance_cm':position_tolerance_cm,'angle_tolerance_degrees':angle_tolerance_degrees,
             'full_affine_lossless':False,'unreal_tested':False,'reader':'independent pinned ufbx process'}
    save(workdir/'summary.json',summary)
    return summary
