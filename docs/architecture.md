# Architecture: exact source, measured derivatives

The system separates decoding decisions from format transport and engine behavior. A decoder exposing a file is not proof that its mesh bindings or animation channels are complete. A writer producing a valid file is not proof that its deformation matches the decoder.

| Layer | Contract | Public implementation status |
| --- | --- | --- |
| Decoder / adapter | Recognized header/ABI, supported compression and curve formats, complete native structures and explicit unsupported markers | Documented private research; binary decoder is not bundled |
| Neutral | Original hierarchy, complete affine local transforms, reference/inverse binds, all influences, materials and native metadata | Public schema plus semantic validator |
| Interchange | Explicit projection/sampling/coordinates; no hidden root, retargeting or influence pruning | Deterministic bounded ASCII FBX writer |
| Independent reader | Reconstruct actual interchange geometry, bindings, local/component poses | Project-owned C harness using separately pinned ufbx |
| Engine import | Inspect destination assets, compression, component poses and final render skinning | Future experiment |
| Validation | Compare each boundary against the authoritative representation, with failures and limits recorded | Synthetic unit and independent round-trip tests |

## Source-of-truth rules

Neutral data is immutable input to a derivative operation. Keep all nine scale/shear values even when a standard skeletal destination only uses a diagonal scale. Preserve constants and identity/default evidence alongside evaluated samples. The public schema is a cleaned, independently versioned interface, not a byte-compatible dump of the private prototype format.

Source identity belongs in an authorized private import manifest when working with external assets. Never publish proprietary fingerprints or source paths merely for reproducibility. Public hashes in the build helper identify open-source dependency files; generated output hashes can identify synthetic derivatives. Hash identity proves bytes, not correctness, authorship or asset rights.

Metadata sidecars preserve unbound tracks and descriptor/model movement information separately from skeleton animation. A sidecar is not an evaluated bone or an excuse to call a projected transform lossless. All body bones, including unweighted attachments, remain in the original hierarchy.

## Matrix and coordinate boundary

The current public executable profile is native centimeters, column vectors, right-handed XYZ algebra, Z-up and a declared negative-Y forward axis. Local matrices are `T * R * S`; full S is stored column-major. World matrices are `parentWorld * local`. Skinning uses each original inverse bind and influence without normalization cleanup.

The public FBX profile retains the same coordinates and bottom-left UV values. It performs no visual axis correction. A future basis conversion must apply the same conjugation to local transforms and inverse binds, transform mesh points, use inverse-transpose for normals, and explicitly handle winding/UV conventions. Engine API multiplication conventions must be verified separately.

## Reproducibility

Object ordering and FBX identifiers are deterministic; the writer has no wall-clock timestamp, random UUID, machine path or external scene host. The synthetic generator is formula-authored, with a documented 12-decimal authoring quantization to suppress platform libm last-bit differences. That fixture policy is not a license to round external source data.

The FBX reader is compiled from an immutable source pin and checked source hashes. Python dependencies are version-pinned; CMake/compiler/OS versions still matter and should be recorded for a measured run. The public workflow reproduces synthetic contracts only. It does not claim cross-platform binary-identical compiler output or private-corpus reproducibility.
