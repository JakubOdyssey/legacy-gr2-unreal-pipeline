# Publication audit

Status: **AUDIT COMPLETE.** This pre-construction record defines the allowed material; the final prepared-content gate is recorded in PUBLICATION_READINESS.md.

This audit was completed before copying or building repository contents. The private development workspace is authoritative and read-only. Publication uses a separate workspace. Its absolute location, original asset names, original file hashes and raw inventory are deliberately omitted from this public report.

## Inventory and classification

A recursive inventory covered **164 files (154,040,223 bytes)**, including hidden files. No reparse-point files were found. SHA256 and modification metadata were recorded privately in the active audit session for a final unchanged-input check; proprietary fingerprints are not published.

| Class | Files | Disposition |
| --- | ---: | --- |
| A — safe and useful without editing | 0 | No private file approved for byte-for-byte publication. |
| B — potentially public after sanitization | 41 | Project-owned tools, research prose and schema concepts. Review selected code; rewrite all prose; publish only aggregate findings. |
| C — third-party source/notices | 23 | Refer to pinned upstreams; do not vendor private third-party copies. |
| D — proprietary assets and descriptors | 15 | Never copy. Includes all source snapshots and prohibited asset extensions. |
| E — directly derived/generated evidence | 79 | Exclude complete neutral geometry, animation/matrix dumps, asset FBX, raw logs and validation payloads. |
| F — uncertain/private build/provenance | 6 | Exclude compiled outputs and private manifests. |

The counts assign every discovered file once. Class B is eligibility for further review, not blanket approval. Category E conservatively excludes whole generated evidence files even if some fields are harmless. Source assets were inventoried without decoding or executing them.

## Approved transformation plan

| Private material category | Public treatment |
| --- | --- |
| Generic matrix, quaternion, hierarchy and skinning logic | Adapt selected project-owned math functions into a path-independent module. No private matrices or samples. |
| Project-owned ASCII FBX serialization | Refactor the generic writer for a new public schema; strip private loading, asset naming, native decoder imports and corpus-specific settings. |
| Project-owned independent-reader C harness | Adapt for explicit CLI paths and safe standalone JSON output; external reader remains a separately pinned dependency. |
| Research reports | Newly written explanations of format investigation, motion separation, representation limits and validation methodology. No source-code quotations from game code. |
| Private numerical results | Only the explicitly approved aggregate counts/errors; state that the private corpus is not shipped or publicly reproducible here. |
| Neutral-format concepts | New generic versioned schema and entirely code-generated synthetic examples. |

All other private tooling is excluded from this release. In particular, asset acquisition, snapshots, game-source tracing, private report generators and GR2 parser adapters are not copied. No public GR2 decoder command is claimed.

## Third-party review

The reviewed native Python reader is upstream Rasetsuu/blendergranny, pinned commit `79b1963ef33df51767cd9ddfd6092846318935ef`. Its checked license is MIT, copyright 2026 ciupix and contributors. Its source and private integration are **not vendored**.

The independent FBX reader is upstream ufbx, pinned commit `fcc5d6ba444cfd3eb80677dba5e37e493941abe5`. Its checked license offers MIT or public-domain alternatives; this project documents the MIT alternative, copyright 2020 Samuli Raivio. No reader source or binary is copied from the private workspace. Optional builds acquire the exact upstream source and preserve its notice outside tracked publication content.

Project-owned refactors and new synthetic data will carry their own license. This does not grant rights in any third-party source asset. Dependency source details and notices are documented separately in THIRD_PARTY.md and NOTICE.md.

## Exclusions and release gate

No original source asset, game source, texture, descriptor, database/server configuration, executable/library, extracted package, generated private geometry, full per-frame animation data, private path, private username or original-asset fingerprint may enter the public tree.

The final guard must scan the entire public workspace before Git initialization and the staged index before committing. Synthetic files must be reproducible from committed code. Readiness remains pending until schema/unit/determinism/round-trip tests and the publication scan pass. No remote creation or push is authorized.

## Preparation-only instruction

The repository owner subsequently reserved Git initialization, the first commit, remote creation and pushing for their own terminal and public identity. This preparation creates **no Git metadata, commits or remote**. The staged guard is supplied and tested with simulated Git plumbing; the owner must run it on their real index after staging. Final content readiness is recorded separately in PUBLICATION_READINESS.md.
