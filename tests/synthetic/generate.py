"""Generate an original seven-joint block figure; no external asset inputs.

Dimensions, topology, weights and motion are authored here from simple formulas.
The small artificial shear is intentionally nonzero and never treated as identity.
"""
import argparse
import copy
import math
from pathlib import Path

from tools.legacy_pipeline import math3d as m
from tools.legacy_pipeline.neutral import canonical_bytes, save


def pose(translation=(0., 0., 0.), scale=(1., 1., 1.)):
    s = m.I9[:]
    for index, value in zip((0,4,8),scale): s[index] = value
    return {'translation':list(translation),'rotation':[0.,0.,0.,1.],'scale_shear':s}


def _generate():
    # Names and geometry are original and intentionally abstract.
    specs = [('origin',-1,pose((0.,0.,32.))),('block_core',0,pose((0.,0.,16.))),
             ('arm_left',1,pose((-15.,0.,0.))),('arm_right',1,pose((15.,0.,0.),(-1.,1.3,.8))),
             ('leg_left',0,pose((-6.,0.,-18.),(1.,1.2,.7))),('leg_right',0,pose((6.,0.,-18.))),
             ('attachment_tip',3,pose((0.,0.,-12.)))]
    specs[1][2]['scale_shear'][3] = 2e-7
    bones = [{'name':n,'parent':p,'rest':t,'inverse_bind':copy.deepcopy(m.I4),'helper':i==6} for i,(n,p,t) in enumerate(specs)]
    worlds = m.world_matrices(bones,[b['rest'] for b in bones])
    for b,w in zip(bones,worlds): b['inverse_bind'] = m.inverse(w)
    mesh={'id':'articulated_blocks','positions':[],'normals':[],'uv0':[],'triangles':[],'skin':[],'face_materials':[]}
    corners=[(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]
    faces=[(0,2,1),(0,3,2),(4,5,6),(4,6,7),(0,1,5),(0,5,4),(3,7,6),(3,6,2),(0,4,7),(0,7,3),(1,2,6),(1,6,5)]
    dimensions=[(8,6,8),(10,5,7),(3,3,10),(3,3,10),(3,4,12),(3,4,12)]
    for bone_index,dims in enumerate(dimensions):
        offset=len(mesh['positions']); normal_matrix=m.inverse(worlds[bone_index])
        for vi,c in enumerate(corners):
            mesh['positions'].append(m.point(worlds[bone_index],[x*d for x,d in zip(c,dims)]))
            # Inverse-transpose normal conversion, then unit normalization.
            n=[sum(normal_matrix[j][i]*c[j] for j in range(3)) for i in range(3)]
            length=math.sqrt(sum(x*x for x in n)); mesh['normals'].append([x/length for x in n])
            mesh['uv0'].append([(c[0]+1)/2,(c[2]+1)/2])
            if bone_index and vi<4:
                mesh['skin'].append([{'bone':bone_index,'weight':.75},{'bone':bones[bone_index]['parent'],'weight':.25}])
            else: mesh['skin'].append([{'bone':bone_index,'weight':1.}])
        negative = bone_index==3
        for face in faces:
            ordered=tuple(reversed(face)) if negative else face
            mesh['triangles'].append([offset+i for i in ordered]); mesh['face_materials'].append('diagnostic_blue')
    animations=[]
    for label,duration,amplitude in [('idle',2.,3.),('stride',1.,28.)]:
        tracks=[]
        for bi,bone in enumerate(bones):
            samples=[]
            for k in range(17):
                t=duration*k/16; p=copy.deepcopy(bone['rest'])
                wave=math.sin(2*math.pi*k/16)
                if bi in (2,3,4,5):
                    angle=math.radians(amplitude*wave*(1 if bi in (2,5) else -1))
                    p['rotation']=[math.sin(angle/2),0.,0.,math.cos(angle/2)]
                if bi==0: p['translation'][2] += (.1 if label=='idle' else .7)*(1-math.cos(4*math.pi*k/16))
                samples.append({'time_seconds':t,'transform':p})
            channels={}
            for component in ('translation','rotation','scale_shear'):
                values=[s['transform'][component] for s in samples]
                constant=all(v==values[0] for v in values)
                ident={'translation':[0.,0.,0.],'rotation':[0.,0.,0.,1.],'scale_shear':m.I9}[component]
                semantics='identity' if constant and values[0]==ident else ('constant' if constant else 'sampled')
                channels[component]={'semantics':semantics,'codec':'synthetic-explicit-v1','format_id':None,
                                     'evidence':'Defined directly by the committed synthetic generator; not inferred from a missing array.',
                                     'payload':{'knots':[0.] if constant else [s['time_seconds'] for s in samples],
                                                'controls':[values[0]] if constant else values}}
            tracks.append({'bone':bi,'interpolation':'linear-translation-scale_shear+slerp-rotation','native_channels':channels,'samples':samples})
        animations.append({'name':label,'duration_seconds':duration,'tracks':tracks})
    return {'format':'legacy-skeletal-neutral','version':'1.0.0',
            'provenance':{'kind':'synthetic','source_id':'original-seven-joint-block-figure','generator_ref':'tests/synthetic/generate.py','license_statement':'Original code-generated fixture, MIT; no third-party asset inputs.'},
            'coordinates':{'units':'cm','vectors':'column','local_order':'T*R*S','scale_shear_layout':'column-major','handedness':'right','up_axis':'+Z','forward_axis':'-Y','uv_origin':'bottom-left'},
            'meshes':[mesh],'skeleton':{'bones':bones},
            'materials':[{'id':'diagnostic_blue','base_color':[.12,.4,.7,1.],'texture_refs':[],'two_sided_hint':False,'alpha_mode_hint':'opaque'}],
            'animations':animations,'motion_sidecar':{'actor_motion_applied':False,'declared_loop_translation':[0.,0.,0.],'descriptor_accumulation':[0.,-17.,0.],
                'unbound_tracks':[{'name':'synthetic_unbound_marker','evidence':'Deliberate unbound metadata, not a bone or actor trajectory.','transform':pose()}],
                'interpretation':'Artificial descriptor value tests separation only. Never add it to local root translation.'}}


def generate():
    # Public fixture authoring policy: 12 decimal places removes libm last-bit
    # differences across platforms. This policy is never applied to source assets.
    def stable(value):
        if isinstance(value, float): return round(value,12) or 0.0
        if isinstance(value, list): return [stable(v) for v in value]
        if isinstance(value, dict): return {k:stable(v) for k,v in value.items()}
        return value
    return stable(_generate())


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=Path('examples/synthetic_asset/neutral.json'))
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args(); data=generate()
    if args.check:
        if not args.output.exists() or args.output.read_bytes()!=canonical_bytes(data):
            parser.exit(1,'Synthetic fixture differs from generator\n')
        print('Synthetic fixture is reproducible')
    else: save(args.output,data)


if __name__=='__main__': main()
