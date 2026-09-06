# Numerical validation

A useful test compares semantics and evaluated deformation, not only array lengths or whether an exporter returned success. The independent reader must not be patched to agree with a mistaken writer convention.

## Boundaries and metrics

Check mesh points, triangle topology, UVs/normals, material groups, exact bone names/parents, reference/inverse-bind agreement and every active weight. Evaluate local transforms and component/world matrices; then skin the original points using the original bindings and compare the resulting positions. Include unweighted attachment bones and endpoints, since a plausible-looking torso does not establish hand/socket correctness.

For vector errors use Euclidean distance in the declared units. Quaternion error is the shortest orientation angle after normalizing, with q and -q treated as the same rotation. RMS and P95 must state the population: the controlled audit pools equally weighted vertex/time observations and includes zero errors. Raw mixed-unit matrix-element errors are diagnostics, not centimeters.

| Target used in private research | Tolerance |
| --- | ---: |
| Static bounds / proportions | ≤0.1% |
| Bind-pose vertex reconstruction | ≤0.1 cm |
| Animation position | ≤0.5 cm |
| Local orientation | ≤0.5° |
| Duration | ≤0.001 s |

These targets are not an automatic permission to discard source structure. The original strict lossless-affine gate failed despite passing finite pose thresholds. Public synthetic integration uses a tighter **0.001 cm / 0.01°** transport check and exact topology/influence membership. It separately reports omitted affine terms and does not label the result lossless.

## Isolating causes

```text
A = full neutral deformation
B = same neutral data, only local off-diagonal S set to zero
C = independently re-imported FBX deformation

C - A = (B - A) + (C - B)    # vector equality; maxima are not additive
```

B must keep translation, quaternion, signed diagonal scale, inverse binds and weights unchanged. Rebuilding binds would compensate for a changed reference and confound the experiment. C's scale/shear reconstruction must use C's own quaternion; otherwise an interpolation-induced rotation difference can be mislabeled as shear.

In the private corpus, controlled local off-diagonal removal produced approximately **0.00000448 cm** maximum vertex change, whereas total run FBX error was approximately **0.3083 cm**. These are different causes and different worst observations. The latter must not be attributed to shear. Full private matrices, per-bone dumps, source hashes and keyframes are excluded from this repository.

## Public regression coverage

The original fixture has 48 vertices, 72 triangles, 7 bones, 68 active influences and two clips. Tests verify its generation, exact counts, inverse binds, constant/identity semantics, signed scale and motion-sidecar separation. Invalid cycles, wrong weight sums, missing tracks, unsupported channels, false identity declarations, non-finite data and unknown schema fields must fail.

Independent integration writes reference, idle and stride FBX files, reads each with a separately compiled ufbx process, and checks all supplied keys plus interval midpoints (33 times per synthetic clip). A deliberately renamed FBX attachment must fail bone-set comparison. Deterministic output is tested by writing twice to different filenames and comparing bytes. The native helper is not a proprietary runtime and does not read GR2.

The initial local synthetic stride test measured **0 weight error**, **0 duration error**, maximum vertex error approximately **0.00000147 cm**, and maximum local orientation error approximately **0.00000171°**. These synthetic results are distinct from the private table in the README. Floating-point angle diagnostics near zero are not a claim of that much physical rotation error.

## Evidence limits

Finite samples do not prove equality over all real-valued times. Synthetic tests do not validate every GR2 encoding or reproduce unavailable game assets. An independent FBX reader is not an Unreal renderer. Standard UE component-transform composition, animation compression, packed skin weights, render-vertex splits, materials, normals and attachments require their own engine test. No hosted GitHub CI run or UE import has been claimed during local repository preparation.
