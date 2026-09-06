# Public neutral format 1.0.0

[neutral-format.schema.json](neutral-format.schema.json) uses JSON Schema Draft 2020-12. The public schema is based on the research representation's concepts, but is a new generic interface; private prototype JSON is not copied and is not automatically compatible.

## Data contracts

| Structure | Required data |
| --- | --- |
| Mesh | Identifier, positions, normals, UV0, explicit triangles, per-face material identifiers, complete positive skin influences |
| Skeleton/bone | Original name, parent index (`-1` for root), full local rest transform, reference inverse bind, explicit helper marker |
| Transform | Translation, xyzw quaternion, all nine scale/shear values |
| Material | Identifier, base color, texture references and explicit unknown/known alpha/two-sided hints |
| Animation | Name, duration, exactly one track per original bone, native channel records and sampled local transforms |
| Native channel | Codec/type identifier, semantic classification, evidence and structured knot/control metadata |
| Sample | Time in seconds and complete local transform, including full scale/shear |
| Motion sidecar | Declared/descriptor movement, unbound records and explicit interpretation; actor motion is not applied |
| Provenance | Synthetic/external source kind, opaque identifier, generator reference and license statement |

The current executable profile uses centimeters, column vectors, `T*R*S`, right-handed Z-up coordinates and bottom-left UVs. The nine S entries are column-major; 4×4 matrices are arrays of rows. Quaternions are unit xyzw. Reference mesh points are already in mesh space and `worldRest * inverseBind` must reconstruct identity within the validator's tolerance. There is no extra implicit model placement in this profile.

## Structural and semantic validation

JSON Schema checks shape, required fields, supported version, dimensions, types and unexpected properties. `validate-neutral` additionally checks finite values, a unique rooted acyclic hierarchy, reference/inverse binds, triangle bounds, material references, positive weights summing to one, complete track coverage, unique ordered sample times and exact endpoints.

Identity/rest/default semantics require explicit evidence. Constant/identity/rest metadata must agree with all evaluated samples; rest values must match the associated reference component. `unsupported` and `absent_unresolved` can be represented by the schema for inspection but fail the executable fidelity gate. No fallback silently generates a missing channel.

The public evaluator supports its declared sampled policy: linear translation and full S, shortest-arc quaternion SLERP. Codec payloads are preserved metadata, not arbitrary decoder programs. The FBX writer uses supplied sample times and refuses nonzero shear unless the caller explicitly authorizes a bounded projection. It currently handles color-only diagnostic materials; external texture reconstruction is not implemented.

The format is intentionally conservative: no opaque base64 buffers, arbitrary machine paths, embedded binaries or private corpus records are required. The only committed full payload is the original [synthetic example](../examples/synthetic_asset/neutral.json), which the guard regenerates and compares. A schema describes data; it does not grant publication rights in any external instance.

Changes that alter coordinate/reference meaning, transform semantics or interpolation require a versioned migration and independent round-trip tests. Additive fields require deliberate schema review rather than silently accepting unknown content.
