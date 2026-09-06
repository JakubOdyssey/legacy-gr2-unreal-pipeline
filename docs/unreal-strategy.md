# Unreal strategy: retain exact source, qualify standard assets

**Recommendation: a hybrid pipeline.** Keep complete neutral data authoritative and generate standard skeletal assets for gameplay when measured fidelity supports them. Introduce an editor importer or custom deformation path only when a specific failure or repeated automation need justifies its implementation and maintenance.

## Destination representation matters

UE's standard raw skeletal tracks contain position vectors, quaternion rotations and scale vectors. FTransform represents those same components, not a free affine/shear matrix. A matrix constructor or matrix-returning method does not expand the stored degrees of freedom. [Raw animation API](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Runtime/Engine/FRawAnimSequenceTrack), [TTransform API](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Runtime/Core/TTransform).

Local and component skeletal poses are represented by FTransform arrays. Full matrices exist later in skinning, but a downstream matrix cannot recover information already discarded during pose evaluation. Rotated children under nonuniformly scaled parents can introduce component shear even if every local transform is TRS. This is a separate risk from tiny off-diagonal values in the original local S. [Component transform API](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Runtime/Engine/FAnimationRuntime), [skinning matrix API](https://dev.epicgames.com/documentation/unreal-engine/API/Runtime/Engine/FSkeletalMeshObject).

## Compare routes by what they solve

| Route | Benefit | Limitation |
| --- | --- | --- |
| Standard FBX | Existing inspection ecosystem and independently tested transport | Projection, Euler interpolation, importer settings and destination behavior need qualification |
| glTF / Interchange | Alternative transport/automation | Core animated glTF nodes use TRS; destination UE pose storage remains unchanged |
| Neutral editor importer | Direct mesh, skeleton, weights and quaternion-track creation with explicit policy | Cannot add arbitrary affine tracks to standard animation assets |
| Helper-node factorization | Two TRS matrix factors can reproduce an affine local matrix algebraically | Component FTransform flattening and blend stability may defeat the intended result |
| Morph/vertex/cache/custom deformer | Can reproduce selected surfaces or directly evaluate source matrices | Runtime, memory, blending, normals, LOD, attachment and cinematic-only tradeoffs |

glTF node matrices must be TRS-decomposable and animated targets use TRS properties, so changing containers is not a shear remedy. [Khronos transformation rules](https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html#transformations).

A neutral editor-only plugin is feasible using skeletal mesh construction, reference-skeleton modification and animation-data-controller APIs. It could remove FBX-specific conversion decisions and improve automation. It still needs source sampling, packed-weight, compression and component-pose validation. No such plugin is implemented in this public release. [Bone track controller](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Runtime/Engine/IAnimationDataController/SetBoneTrackKeys), [skeletal mesh build interfaces](https://dev.epicgames.com/documentation/unreal-engine/API/Developer/MeshUtilities/IMeshUtilities).

## Why helpers are not the default

For column vectors, a signed SVD can factor `S = U D Vᵀ` and represent `T R S` using a parent `T (R U) D` and child `Vᵀ`. This is exact under full matrix multiplication to numerical precision. It is not proof that a standard UE component pose can keep the resulting shear. Near-repeated singular values can also produce unstable factor bases between clips, even when the composed transforms barely differ.

Private research measured the selected original off-diagonal contribution at approximately 0.00000448 cm maximum vertex displacement. That does not justify a second permanent rig or runtime deformer by itself. New meshes may weight previously unused helpers and expose larger inherited scaling effects, so upgraded characters require new measurements rather than inheriting the old verdict.

## Next engine experiment

Use a version-pinned editor and a blank validation project: one authorized/original test character, its original bones/skin, two clips and one diagnostic material. No environment, gameplay, retargeting or actor-motion baking. Read actual imported reference data, raw and compressed animation, component poses, skinning matrices and source-point-mapped final vertices. Check helpers and signed/nonuniform scales explicitly.

A passing independent FBX test is a reason to perform this engine experiment, not evidence that it already passed. Preserve exact neutral/native sidecars for audit and for later cinematic/custom paths if a visible or structural problem is measured. This repository's CI requires no engine installation and makes no claim of completed Unreal integration.
