# Animation semantics before export

An animation channel is not just an array of samples. Its meaning can be explicit identity, a constant, a sampled/compressed curve, a format-defined rest/default value, an unresolved absence or an unsupported encoding. Those states must remain distinguishable through decoding and validation.

## Default and constant channels

An explicit identity record can correctly contain no varying keys. Once its format semantics are established, identity is a valid evaluated component. An empty array by itself is not that evidence. Likewise, a missing rotation does not authorize an identity quaternion, and missing scale/shear does not authorize discarding nonuniform scale.

A constant may be stored as one control plus degree/type metadata, rather than a regular sampled curve. Preserve that value and its encoding; do not manufacture changing samples. To resolve rest semantics, require a documented source rule and compare the resolved component with the associated reference pose. In the public schema, both identity and rest semantics require evidence text and values consistent with that claim.

Private research identified zero-key legacy identity records that a convenience reader had represented as no data. A bounded adapter restored the distinction only after inspecting the original record semantics. This public release documents the finding but does not include the private adapter, proprietary channel dumps or copied game source.

## Local skeleton versus actor motion

Body animation describes local bone poses. A model/control system may separately extract movement, gameplay may scale or constrain it, and networking may determine world position. Matching numerical values in a descriptor and an animation group do not prove both should be added to the root.

MSA-like accumulation fields can be parsed and stored without being consumed as a movement vector on the active runtime path. Trace the reader, storage and consumers before deciding whether a field drives speed, displacement, selection, authoring metadata or nothing in the relevant path. Keep opaque runtime integration unqualified when the allowed evidence cannot reproduce it.

An unbound transform track is not automatically an extra skeletal root or motion extractor. Preserve it as explicit sidecar data until binding/group behavior establishes how it is consumed. An unknown historical authoring purpose need not block an in-place body export if non-consumption by the qualified body binding is established and the record is retained separately.

The synthetic fixture demonstrates these boundaries with seven body tracks, an unbound marker and an intentionally unrelated descriptor vector. Its root has original procedural vertical motion; horizontal actor displacement is never synthesized from the sidecar. The validator rejects missing body tracks instead of filling them from the reference by default.
