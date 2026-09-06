"""Deterministic bounded ASCII FBX 7.4 writer, adapted from project-owned tooling.

No retargeting, mesh cleanup, actor motion, resampling or scene-host dependency.
Nonzero local off-diagonal S requires explicit projection authorization.
"""
import hashlib
import json
import math
from pathlib import Path

from . import math3d as m
from .neutral import audit_transform, evaluate, validate

TICKS = 46186158000
def number(x): return str(x) if isinstance(x,int) else format(float(x),'.17g')
def quote(x): return json.dumps(str(x),ensure_ascii=True)
def flat(matrix): return [matrix[r][c] for c in range(4) for r in range(4)]
def array(name,values):
    values=list(values)
    return f'{name}: *{len(values)} {{ a: '+','.join(number(x) for x in values)+' }\n'
def prop(name,kind,values,flags='A'):
    return 'P: '+','.join([quote(name),quote(kind),'""',quote(flags)]+[number(v) if isinstance(v,(int,float)) else quote(v) for v in values])+'\n'


def write_fbx(asset, output, clip_name=None, allow_projection=False, max_shear=0.):
    if not math.isfinite(max_shear) or max_shear < 0:
        raise ValueError('Projection bound must be finite and nonnegative')
    validate(asset)
    audit=audit_transform(asset)
    relevant=['rest']+([clip_name] if clip_name else [])
    if any(n not in audit['clips'] for n in relevant): raise ValueError('Unknown clip')
    loss=max(audit['clips'][n]['max_off_diagonal'] for n in relevant)
    if loss and (not allow_projection or loss>max_shear):
        raise ValueError(f'Active shear {loss:.9g} requires explicit projection and a sufficient --max-shear bound')
    bones=asset['skeleton']['bones']
    clip=next((c for c in asset['animations'] if c['name']==clip_name),None)
    duration=clip['duration_seconds'] if clip else 0.
    objects=[];connections=[];definitions={};serial=100
    def newid():
        nonlocal serial
        serial+=1;return serial
    def obj(kind,id,name,sub,body):
        objects.append(f'{kind}: {id}, {quote(kind+"::"+name)}, {quote(sub)} {{\n{body}\n}}\n')
        definitions[kind]=definitions.get(kind,0)+1
    def conn(a,b,p=None):
        connections.append('C: '+','.join(['"OP"' if p else '"OO"',str(a),str(b)]+([quote(p)] if p else [])))
    bids=[newid() for _ in bones]
    world=m.world_matrices(bones,[b['rest'] for b in bones]);pose_nodes=[]
    for i,b in enumerate(bones):
        t=b['rest']
        props=prop('Lcl Translation','Lcl Translation',t['translation'])+prop('Lcl Rotation','Lcl Rotation',m.euler_xyz(t['rotation']))+prop('Lcl Scaling','Lcl Scaling',[t['scale_shear'][j] for j in (0,4,8)])
        props+=prop('RotationOrder','enum',[0],'')+prop('RotationActive','bool',[1],'')+prop('InheritType','enum',[1],'')
        obj('Model',bids[i],b['name'],'LimbNode','Version: 232\nProperties70: {\n'+props+'}\nShading: T\nCulling: "CullingOff"')
        aid=newid();obj('NodeAttribute',aid,b['name'],'LimbNode','TypeFlags: "Skeleton"\nProperties70: {\n'+prop('Size','double',[1.],'')+'}')
        conn(aid,bids[i]);conn(bids[i],bids[b['parent']] if b['parent']>=0 else 0)
        pose_nodes.append((bids[i],world[i]))
    matids={}
    for material in asset['materials']:
        if material['texture_refs']: raise ValueError('Public writer currently supports diagnostic color materials only')
        mid=newid();matids[material['id']]=mid
        color=material['base_color']; props=prop('DiffuseColor','Color',color[:3])+prop('DiffuseFactor','Number',[1.])+prop('TransparencyFactor','Number',[1-color[3]])
        obj('Material',mid,material['id'],'','Version: 102\nShadingModel: "lambert"\nMultiLayer: 0\nProperties70: {\n'+props+'}')
    for mesh in asset['meshes']:
        mid,gid,sid=newid(),newid(),newid()
        obj('Model',mid,mesh['id'],'Mesh','Version: 232\nProperties70: {\n'+prop('Lcl Translation','Lcl Translation',[0.,0.,0.])+prop('Lcl Rotation','Lcl Rotation',[0.,0.,0.])+prop('Lcl Scaling','Lcl Scaling',[1.,1.,1.])+prop('InheritType','enum',[1],'')+'}\nShading: T\nCulling: "CullingOff"')
        conn(mid,0);conn(gid,mid);pose_nodes.append((mid,m.I4))
        indices=[v if j!=2 else -v-1 for f in mesh['triangles'] for j,v in enumerate(f)]
        geometry='GeometryVersion: 124\n'+array('Vertices',[x for p in mesh['positions'] for x in p])+array('PolygonVertexIndex',indices)
        geometry+='LayerElementNormal: 0 { Version: 101\nName: ""\nMappingInformationType: "ByVertice"\nReferenceInformationType: "Direct"\n'+array('Normals',[x for v in mesh['normals'] for x in v])+'}\n'
        geometry+='LayerElementUV: 0 { Version: 101\nName: "UV0"\nMappingInformationType: "ByVertice"\nReferenceInformationType: "Direct"\n'+array('UV',[x for uv in mesh['uv0'] for x in uv])+'}\n'
        matnames=list(matids)
        geometry+='LayerElementMaterial: 0 { Version: 101\nName: ""\nMappingInformationType: "ByPolygon"\nReferenceInformationType: "IndexToDirect"\n'+array('Materials',[matnames.index(x) for x in mesh['face_materials']])+'}\n'
        geometry+='Layer: 0 { Version: 100\n'+''.join('LayerElement: { Type: '+quote(t)+'\nTypedIndex: 0 }\n' for t in ('LayerElementNormal','LayerElementUV','LayerElementMaterial'))+'}'
        obj('Geometry',gid,mesh['id'],'Mesh',geometry)
        for id in matids.values(): conn(id,mid)
        obj('Deformer',sid,mesh['id'],'Skin','Version: 101\nSkinningType: "Linear"');conn(sid,gid)
        for bi,b in enumerate(bones):
            weights=[(vi,w['weight']) for vi,ws in enumerate(mesh['skin']) for w in ws if w['bone']==bi]
            if not weights: continue  # No bone node is removed; only empty clusters are omitted.
            cid=newid();data='Version: 100\nUserData: "", ""\nMode: "Normalize"\n'
            data+=array('Indexes',[vi for vi,w in weights])+array('Weights',[w for vi,w in weights])
            data+=array('Transform',flat(b['inverse_bind']))+array('TransformLink',flat(m.inverse(b['inverse_bind'])))
            obj('Deformer',cid,mesh['id']+'_'+b['name'],'Cluster',data);conn(cid,sid);conn(bids[bi],cid)
    pose='Type: "BindPose"\nVersion: 100\nNbPoseNodes: '+str(len(pose_nodes))+'\n'
    for id,mat in pose_nodes: pose+='PoseNode: { Node: '+str(id)+'\n'+array('Matrix',flat(mat))+'}\n'
    obj('Pose',newid(),'Reference','BindPose',pose)
    if clip:
        stack,layer=newid(),newid()
        obj('AnimationStack',stack,clip['name'],'','Properties70: {\n'+''.join(prop(k,'KTime',[v],'') for k,v in [('LocalStart',0),('LocalStop',round(duration*TICKS)),('ReferenceStart',0),('ReferenceStop',round(duration*TICKS))])+'}')
        obj('AnimationLayer',layer,'Base','','Properties70: {\n'+prop('Weight','Number',[100.])+prop('BlendMode','enum',[1],'')+'}');conn(layer,stack)
        times=sorted({s['time_seconds'] for t in clip['tracks'] for s in t['samples']})
        frames=[evaluate(clip,t,len(bones)) for t in times]
        for bi,bone in enumerate(bones):
            local=[f[bi] for f in frames];angles=[]
            for t in local:
                a=m.euler_xyz(t['rotation'])
                if angles:
                    candidates=[a,[a[0]+180,180-a[1],a[2]+180]]
                    candidates=[[x+360*round((p-x)/360) for x,p in zip(c,angles[-1])] for c in candidates]
                    a=min(candidates,key=lambda c:sum((x-p)**2 for x,p in zip(c,angles[-1])))
                angles.append(a)
            channels={'Lcl Translation':[x['translation'] for x in local],'Lcl Rotation':angles,'Lcl Scaling':[[x['scale_shear'][j] for j in (0,4,8)] for x in local]}
            for property_name,values in channels.items():
                nid=newid();obj('AnimationCurveNode',nid,bone['name']+'_'+property_name,'','Properties70: {\n'+''.join(prop('d|'+axis,'Number',[values[0][i]]) for i,axis in enumerate('XYZ'))+'}')
                conn(nid,layer);conn(nid,bids[bi],property_name)
                for i,axis in enumerate('XYZ'):
                    vals=[v[i] for v in values];kt=times
                    if all(v==vals[0] for v in vals): vals=vals[:1];kt=times[:1]
                    cid=newid();data='Default: '+number(vals[0])+'\nKeyVer: 4008\n'+array('KeyTime',[round(t*TICKS) for t in kt])+array('KeyValueFloat',vals)+array('KeyAttrFlags',[4])+array('KeyAttrDataFloat',[0.,0.,0.,0.])+array('KeyAttrRefCount',[len(vals)])
                    obj('AnimationCurve',cid,bone['name']+'_'+property_name+'_'+axis,'',data);conn(cid,nid,'d|'+axis)
    header='; FBX 7.4.0 project file\nFBXHeaderExtension: { FBXHeaderVersion: 1003\nFBXVersion: 7400\nCreator: "Legacy skeletal neutral writer 0.1" }\n'
    header+='GlobalSettings: { Version: 1000\nProperties70: {\n'+''.join(prop(k,'int',[v],'') for k,v in [('UpAxis',2),('UpAxisSign',1),('FrontAxis',1),('FrontAxisSign',-1),('CoordAxis',0),('CoordAxisSign',1),('TimeMode',3)])+prop('UnitScaleFactor','double',[1.],'')+prop('OriginalUnitScaleFactor','double',[1.],'')+'}}\n'
    header+='Documents: { Count: 1\nDocument: 1, "Scene", "Scene" { RootNode: 0 } }\nReferences: {}\nDefinitions: { Version: 100\nCount: '+str(sum(definitions.values()))+'\n'+''.join('ObjectType: '+quote(k)+' { Count: '+str(v)+' }\n' for k,v in definitions.items())+'}\n'
    content=header+'Objects: {\n'+''.join(objects)+'}\nConnections: {\n'+'\n'.join(connections)+'\n}\nTakes: { Current: "" }\n'
    output=Path(output);output.parent.mkdir(parents=True,exist_ok=True);payload=content.encode('utf-8');output.write_bytes(payload)
    return {'status':'WRITTEN_REQUIRES_INDEPENDENT_VALIDATION','sha256':hashlib.sha256(payload).hexdigest(),'bytes':len(payload),'max_projected_off_diagonal':loss,'actor_motion_applied':False,'clip':clip_name,'audit':audit}
