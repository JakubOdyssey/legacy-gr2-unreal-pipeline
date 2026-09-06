# GR2 investigation notes

GR2 is a family of legacy skeletal asset containers rather than one universally interchangeable mesh format. Compatibility work must establish the exact file header/version, byte order, pointer width, section table, compression identifiers, relocation/fixup records and reflected structure types of a selected corpus before interpreting higher-level data.

The private investigation used an audited pin of an open-source native Python reader. It inspected legacy compressed sections and parser-visible structures without invoking a proprietary Granny SDK/runtime. That observation is scoped to the selected corpus and reader; it is not a general format compatibility guarantee. The public repository references the upstream project and its license, but ships no decoder or private integration. [Dependency provenance](../THIRD_PARTY.md).

## What to inspect before conversion

| Structure | Questions that affect correctness |
| --- | --- |
| Mesh buffers | Vertex stride/types, index width, normals/UVs, material groups, optional attributes and actual counts |
| Skeleton | Names, parents, effective transform flags, full scale/shear, reference placement and inverse binds |
| Skin bindings | Per-mesh palette to skeleton mapping, all influence lanes, active weights and invalid indices |
| Curves | Exact encoding identifier, degree, dimensions, knots, control storage, constants/defaults and unsupported branches |
| Animation groups | Binding target, local body tracks, unbound records, placement and declared motion metadata |
| Materials | Original identifiers, external references and unresolved fields, without inventing modern shader meaning |

Keep decoded structures separate from a convenience API's return values. A parser returning `None` may have erased a useful distinction between a recognized zero-key identity record and an unsupported/absent curve. Classification requires original type/metadata evidence, not whether the pose looks reasonable.

Inspect the source paths that implement decoding, compression dispatch and fallback behavior. Identify any silently skipped types, indirect/shared storage and dimensional assumptions. A correct mesh does not establish rig or animation correctness. Stop on unresolved meaningful channels or inconsistent skin palettes.

The public notes intentionally contain no private binary offsets, source snippets, original filenames, hexdumps, hashes, mesh buffers or animation keys. They describe a repeatable investigation method, not instructions for obtaining/distributing copyrighted assets or bypassing access restrictions.
