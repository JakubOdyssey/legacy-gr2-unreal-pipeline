"""Strict schema plus semantic validation; no binary decoder or implicit defaults."""
import bisect
import json
import math
from pathlib import Path

from . import math3d as m

SCHEMA = Path(__file__).resolve().parents[2] / 'schemas' / 'neutral-format.schema.json'


def load(path):
    def reject(value):
        raise ValueError(f"Non-finite JSON number: {value}")
    return json.loads(Path(path).read_text(encoding='utf-8'), parse_constant=reject)


def canonical_bytes(value):
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True, allow_nan=False)+'\n').encode('utf-8')


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_bytes(value))


def _finite(value):
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("Non-finite data")
    if isinstance(value, dict):
        for child in value.values(): _finite(child)
    if isinstance(value, list):
        for child in value: _finite(child)


def evaluate(clip, time, bone_count):
    if not 0 <= time <= clip['duration_seconds']:
        raise ValueError("Time outside clip")
    result = [None] * bone_count
    for track in clip['tracks']:
        keys = track['samples']; times = [s['time_seconds'] for s in keys]
        i = bisect.bisect_right(times, time) - 1
        if i == len(keys)-1 or time == times[i]:
            value = keys[i]['transform']
        else:
            alpha = (time-times[i])/(times[i+1]-times[i])
            value = m.interpolate(keys[i]['transform'], keys[i+1]['transform'], alpha)
        result[track['bone']] = value
    if any(t is None for t in result):
        raise ValueError("Missing body track; no implicit rest/identity fill")
    return result


def validate(asset):
    from jsonschema import Draft202012Validator
    schema = load(SCHEMA)
    Draft202012Validator.check_schema(schema)
    errors = sorted(Draft202012Validator(schema).iter_errors(asset), key=lambda e: str(e.json_path))
    if errors:
        raise ValueError(f"Schema: {errors[0].json_path}: {errors[0].message}")
    _finite(asset)
    bones = asset['skeleton']['bones']; count = len(bones)
    names = [b['name'] for b in bones]
    if len(set(names)) != count or sum(b['parent'] == -1 for b in bones) != 1:
        raise ValueError("Expected unique bones and exactly one root")
    worlds = m.world_matrices(bones, [b['rest'] for b in bones])
    bind_matrix_error = 0.
    for bone, world in zip(bones, worlds):
        if abs(sum(v*v for v in bone['rest']['rotation'])-1) > 1e-5:
            raise ValueError("Rest quaternion is not normalized")
        m.inverse(m.transform(bone['rest']))
        bind_matrix_error = max(bind_matrix_error, m.matrix_error(m.multiply(world, bone['inverse_bind']), m.I4))
    if bind_matrix_error > 1e-5:
        raise ValueError("Reference / inverse bind disagreement")
    material_ids = {mat['id'] for mat in asset['materials']}
    if len(material_ids) != len(asset['materials']):
        raise ValueError("Duplicate materials")
    mesh_ids = [mesh['id'] for mesh in asset['meshes']]
    if len(set(mesh_ids)) != len(mesh_ids): raise ValueError("Duplicate mesh IDs")
    influences, bind_vertex_error = 0, 0.
    for mesh in asset['meshes']:
        n = len(mesh['positions'])
        if any(len(mesh[k]) != n for k in ('normals', 'uv0', 'skin')):
            raise ValueError("Vertex attribute lengths differ")
        for face in mesh['triangles']:
            if len(set(face)) != 3 or any(i >= n for i in face): raise ValueError("Invalid triangle")
        if len(mesh['face_materials']) != len(mesh['triangles']) or not set(mesh['face_materials']) <= material_ids:
            raise ValueError("Invalid material groups")
        for weights in mesh['skin']:
            if len({w['bone'] for w in weights}) != len(weights) or any(w['bone'] >= count for w in weights):
                raise ValueError("Duplicate/out-of-range skin influence")
            if abs(sum(w['weight'] for w in weights)-1) > 1e-7: raise ValueError("Weights do not sum to one")
            influences += len(weights)
        for p, q in zip(mesh['positions'], m.skin(mesh, bones, worlds)):
            bind_vertex_error = max(bind_vertex_error, m.distance(p, q))
    clip_names = [c['name'] for c in asset['animations']]
    if len(set(clip_names)) != len(clip_names): raise ValueError("Duplicate clip names")
    for clip in asset['animations']:
        if sorted(t['bone'] for t in clip['tracks']) != list(range(count)):
            raise ValueError("Every original bone needs exactly one track")
        for track in clip['tracks']:
            times = [s['time_seconds'] for s in track['samples']]
            if times[0] != 0 or times[-1] != clip['duration_seconds'] or any(a >= b for a,b in zip(times, times[1:])):
                raise ValueError("Samples need ordered unique times and exact endpoints")
            for sample in track['samples']:
                if abs(sum(v*v for v in sample['transform']['rotation'])-1) > 1e-5:
                    raise ValueError("Animation quaternion is not normalized")
                m.inverse(m.transform(sample['transform']))
            for component, meta in track['native_channels'].items():
                semantics = meta['semantics']
                if semantics in ('unsupported', 'absent_unresolved'):
                    raise ValueError("Unexplained channel semantics")
                values = [s['transform'][component] for s in track['samples']]
                if meta['codec'] == 'synthetic-explicit-v1':
                    expected_controls = [values[0]] if semantics in ('constant','identity','rest') else values
                    expected_knots = [0.] if semantics in ('constant','identity','rest') else times
                    if meta['payload'] != {'knots':expected_knots,'controls':expected_controls}:
                        raise ValueError('Synthetic native metadata contradicts evaluated samples')
                if semantics in ('constant', 'identity', 'rest') and any(v != values[0] for v in values):
                    raise ValueError("Constant channel metadata contradicts samples")
                if semantics == 'identity':
                    identity = {'translation':[0.,0.,0.], 'rotation':[0.,0.,0.,1.], 'scale_shear':m.I9}[component]
                    if values[0] != identity: raise ValueError("Identity channel has non-identity value")
                if semantics == 'rest' and values[0] != bones[track['bone']]['rest'][component]:
                    raise ValueError("Rest semantic contradicts explicit reference")
                if semantics in ('rest', 'identity') and not meta['evidence']:
                    raise ValueError("Default semantics require evidence")
    return {'meshes':len(asset['meshes']), 'vertices':sum(len(x['positions']) for x in asset['meshes']),
            'triangles':sum(len(x['triangles']) for x in asset['meshes']), 'bones':count, 'influences':influences,
            'clips':len(asset['animations']), 'bind_matrix_error':bind_matrix_error, 'bind_vertex_error_cm':bind_vertex_error}


def audit_transform(asset):
    validate(asset)
    bones = asset['skeleton']['bones']; results = {}
    clips = [('rest', [([b['rest'] for b in bones], None)])]
    for clip in asset['animations']:
        times = sorted({s['time_seconds'] for t in clip['tracks'] for s in t['samples']})
        clips.append((clip['name'], [(evaluate(clip,t,len(bones)),t) for t in times]))
    for label, frames in clips:
        errors, maximum_s, affected = [], 0., set()
        for local, time in frames:
            for i, t in enumerate(local):
                magnitude = max(abs(t['scale_shear'][j]) for j in m.OFF_DIAGONAL)
                maximum_s = max(maximum_s, magnitude)
                if magnitude: affected.add(bones[i]['name'])
            a = m.world_matrices(bones, local); b = m.world_matrices(bones, [m.project_trs(t) for t in local])
            for mesh in asset['meshes']:
                errors.extend(m.distance(p,q) for p,q in zip(m.skin(mesh,bones,a),m.skin(mesh,bones,b)))
        values = sorted(errors)
        results[label] = {'samples':len(frames),'max_off_diagonal':maximum_s,'affected_bones':sorted(affected),
                          'max_vertex_error_cm':max(errors),'rms_vertex_error_cm':math.sqrt(math.fsum(e*e for e in errors)/len(errors)),
                          'p95_vertex_error_cm':values[math.ceil(.95*len(values))-1]}
    return {'comparison':'full neutral vs off-diagonal-only removal; identical inverse binds/weights', 'measured_samples_only':True, 'clips':results}
