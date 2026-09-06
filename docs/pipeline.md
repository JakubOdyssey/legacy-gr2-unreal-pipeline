# Pipeline and implemented CLI

## Research flow

1. **Decode:** qualify the file ABI, section compression, reflected structures and curves. Preserve failure/unsupported markers. No binary decoder is included in this public release.
2. **Normalize without erasing evidence:** state coordinates, quaternion ordering, units, binding maps and default semantics. Normalization must not erase original affine/native data.
3. **Neutral:** validate the public schema and semantic constraints. Reject invalid hierarchy, inconsistent binds, invalid weights, missing body tracks, unexplained channels or contradictory identity/rest claims.
4. **TRS projection:** compare full affine deformation against changing only local S off-diagonals. Retain signed diagonal scales and original inverse binds. Require explicit caller authorization and a bound before writing a projected file.
5. **FBX:** emit one original skeleton, all geometry and influences, diagnostic materials and optionally one clip. Use existing sample times and continuous Euler representatives; do not retarget or bake actor movement.
6. **Independent reader:** run the separately compiled ufbx harness with external-file loading and weight cleanup disabled. Compare the actual decoded topology, bindings, local/component transforms and skinned vertices.
7. **Future Unreal validation:** compare imported raw/compressed animation and final engine component/skinning output against neutral, rather than assuming that independent FBX validation proves engine fidelity.

## Current commands

All commands use `python -B -m tools.legacy_pipeline COMMAND neutral.json`.

| Command | Implemented behavior | Deliberate scope limit |
| --- | --- | --- |
| `inspect` | Schema/semantic validation and aggregate neutral statistics | Does not identify/decode GR2 files |
| `validate-neutral` | Strict schema plus hierarchy, reference, weights and channel checks | One defined coordinate/reference profile; unsupported channels fail |
| `audit-transform` | Full-affine versus off-diagonal-only removal; max/RMS/P95 over supplied sample times | Finite source-sample audit, no original runtime oracle |
| `write-fbx` | Deterministic FBX 7.4 ASCII, all meshes/skin/bones, optional named clip | Diagnostic color materials only; no glTF, texture import, source spline decoder or automatic resampling |
| `validate-fbx` | Separate ufbx process, reference/topology/influence checks and key/midpoint pose comparisons | Requires explicitly supplied locally built reader; no Unreal execution |

`write-fbx` requires `--output`; `--clip` selects a clip. With no clip it writes reference geometry and skeleton. Every export retains the full mesh; separate mesh-free animation output can be added after its own tests. `--allow-trs-projection --max-shear VALUE` is an explicit numerical representation choice. The default rejects every nonzero off-diagonal, and the source JSON is never changed.

`validate-fbx` requires `--fbx`, `--reader` and `--workdir`, plus `--clip` for animation. It writes a readback and aggregate summary to the requested work directory. Use ignored local output locations. It rejects changes to topology/material groups/bindings, unexpected bones, reader adjustments/warnings, lost signed scales and excessive pose errors. Reader failure/timeout is a failed attempt, not a pass.

## Sampling and claims

The public neutral profile evaluates translation and the complete S matrix linearly and quaternions by shortest-arc SLERP. Native metadata is retained but arbitrary codec payloads are not executed. FBX is written at the union of provided sample times with linear Euler curves; these interpolation rules are not mathematically identical in general. Intermediate times must therefore be tested. A degree-0 source constant does not need invented changing samples to explain its semantics.

The shipped fixture's rotations are intentionally simple and its source samples include exact endpoints. Its small error does not establish a universal sample rate. Private research separately showed that an initially insufficient rate had to be increased after measured between-key errors. New schedules require a stated policy and a comparison against native source evaluation.

Outputs marked `WRITTEN_REQUIRES_INDEPENDENT_VALIDATION` have not passed a reader gate. `PASS_NUMERICAL_SAMPLED` means only the reported finite sample/tolerance comparison passed. Neither label means arbitrary-time affine equality or UE production readiness.
