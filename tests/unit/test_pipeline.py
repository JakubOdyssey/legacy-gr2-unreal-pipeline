import copy
import math
import os
from pathlib import Path
import tempfile
import unittest

from tests.synthetic.generate import generate
from tools.legacy_pipeline import math3d as m
from tools.legacy_pipeline.fbx import write_fbx
from tools.legacy_pipeline.neutral import audit_transform, canonical_bytes, evaluate, validate
from tools.legacy_pipeline.roundtrip import validate_fbx

ROOT=Path(__file__).resolve().parents[2]


class NeutralTests(unittest.TestCase):
    def setUp(self): self.asset=generate()

    def test_original_fixture_matches_generator(self):
        self.assertEqual((ROOT/'examples/synthetic_asset/neutral.json').read_bytes(),canonical_bytes(self.asset))

    def test_statistics_and_inverse_bind(self):
        result=validate(self.asset)
        self.assertEqual((result['vertices'],result['triangles'],result['bones'],result['influences']),(48,72,7,68))
        self.assertLess(result['bind_vertex_error_cm'],1e-8)

    def test_invalid_hierarchy(self):
        self.asset['skeleton']['bones'][1]['parent']=2
        with self.assertRaisesRegex(ValueError,'cycle'): validate(self.asset)

    def test_bad_weight_rejected(self):
        self.asset['meshes'][0]['skin'][0][0]['weight']=.5
        with self.assertRaisesRegex(ValueError,'sum'): validate(self.asset)

    def test_missing_track_is_not_filled(self):
        self.asset['animations'][0]['tracks'].pop()
        with self.assertRaisesRegex(ValueError,'exactly one track'): validate(self.asset)

    def test_unknown_curve_is_not_filled(self):
        self.asset['animations'][0]['tracks'][0]['native_channels']['rotation']['semantics']='unsupported'
        with self.assertRaisesRegex(ValueError,'Unexplained'): validate(self.asset)

    def test_false_identity_is_not_accepted(self):
        self.asset['animations'][0]['tracks'][0]['native_channels']['translation']['semantics']='identity'
        with self.assertRaises(ValueError): validate(self.asset)

    def test_native_constant_payload_is_verified(self):
        self.asset['animations'][0]['tracks'][0]['native_channels']['rotation']['payload']['controls'][0][3]=.5
        with self.assertRaisesRegex(ValueError,'metadata contradicts'): validate(self.asset)

    def test_nonfinite_and_unknown_field(self):
        self.asset['meshes'][0]['positions'][0][0]=float('nan')
        with self.assertRaises(ValueError): validate(self.asset)
        self.asset=generate();self.asset['silent_extra']=42
        with self.assertRaisesRegex(ValueError,'Schema'): validate(self.asset)

    def test_negative_and_nonuniform_scale_retained(self):
        local=self.asset['skeleton']['bones'][3]['rest']
        self.assertEqual([local['scale_shear'][i] for i in (0,4,8)],[-1.,1.3,.8])
        self.assertLess(m.matrix_error(m.multiply(m.transform(local),m.inverse(m.transform(local))),m.I4),1e-10)

    def test_root_motion_sidecar_is_not_applied(self):
        clip=self.asset['animations'][1]
        a=evaluate(clip,0,7)[0]['translation'];b=evaluate(clip,clip['duration_seconds'],7)[0]['translation']
        self.assertEqual(a[:2],b[:2]);self.assertEqual(a[2],b[2])
        self.assertNotEqual(self.asset['motion_sidecar']['descriptor_accumulation'],[0.,0.,0.])

    def test_controlled_shear_audit_and_no_mutation(self):
        before=canonical_bytes(self.asset);result=audit_transform(self.asset)
        self.assertEqual(before,canonical_bytes(self.asset))
        self.assertGreater(result['clips']['stride']['max_vertex_error_cm'],0)
        self.assertLess(result['clips']['stride']['max_vertex_error_cm'],.00001)

    def test_slerp_antipodal(self):
        self.assertLess(m.quaternion_angle(m.slerp([0,0,0,1],[0,0,0,-1],.5),[0,0,0,1]),1e-6)

    def test_writer_refuses_implicit_projection(self):
        with self.assertRaisesRegex(ValueError,'requires explicit'): write_fbx(self.asset,ROOT/'.local/refused.fbx')

    def test_nonfinite_projection_bound_rejected(self):
        with self.assertRaisesRegex(ValueError,'finite'): write_fbx(self.asset,ROOT/'.local/refused.fbx',allow_projection=True,max_shear=float('nan'))

    def test_deterministic_writer_no_source_changes(self):
        work=ROOT/'.local/tests';work.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=work) as d:
            first=Path(d)/'first.fbx';second=Path(d)/'second.fbx';before=canonical_bytes(self.asset)
            write_fbx(self.asset,first,'stride',True,1e-6);write_fbx(self.asset,second,'stride',True,1e-6)
            self.assertEqual(first.read_bytes(),second.read_bytes());self.assertEqual(before,canonical_bytes(self.asset))


class IndependentRoundtripTests(unittest.TestCase):
    def test_body_idle_stride_and_corruption(self):
        reader=os.environ.get('UFBX_AUDIT')
        if not reader:
            if os.environ.get('REQUIRE_UFBX')=='1': self.fail('CI requires a built independent reader')
            self.skipTest('Build reader and set UFBX_AUDIT for the independent integration test')
        asset=generate();work=ROOT/'.local/tests';work.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=work) as d:
            for clip in (None,'idle','stride'):
                label=clip or 'body';path=Path(d)/(label+'.fbx')
                write_fbx(asset,path,clip,True,1e-6)
                result=validate_fbx(asset,path,reader,Path(d)/label,clip)
                self.assertEqual(result['status'],'PASS_NUMERICAL_SAMPLED')
                self.assertEqual(result['errors']['weights'],0)
                self.assertLess(result['errors']['skinned_vertex_cm'],.00001)
            altered=path.read_text().replace('Model::attachment_tip','Model::removed_tip')
            path.write_text(altered)
            with self.assertRaisesRegex(ValueError,'Bone set changed'):
                validate_fbx(asset,path,reader,Path(d)/'negative-test','stride')


if __name__=='__main__': unittest.main()
