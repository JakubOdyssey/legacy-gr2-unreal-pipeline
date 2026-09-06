# Development history and evidence boundaries

This is a sanitized engineering narrative, not an internal workspace dump. It contains no source asset identities, private paths or raw animation evidence.

| Milestone | Engineering result | Scope/limitation |
| --- | --- | --- |
| Asset/loader inspection | Identified separate mesh, animation, material, map and runtime concerns before conversion | Broader scene/game data excluded from this public release |
| Decoder selection | Reviewed and pinned an open-source native reader; avoided proprietary runtime use | License of a decoder does not clear rights in assets |
| Body extraction | Mesh, skeleton, attachment and skin integrity qualified on one private character | No private body data distributed |
| Animation semantics | Distinguished legacy explicit identity records from genuinely unexplained channels | Private adapter not bundled; synthetic semantic checks are public |
| Motion investigation | Separated body animation from model/group/descriptor and actor movement | No guessed world trajectory baked into the skeleton |
| Neutral and FBX | Complete neutral source preserved; deterministic writer tested with independent reader | An incorrect initial bind convention was found and corrected through readback |
| Interpolation testing | Between-key errors revealed an insufficient sampling schedule | A refined schedule passed finite numeric thresholds; no all-time equality claim |
| Affine/TRS audit | Strict affine lossless gate failed, followed by controlled measurement of the omitted local terms | Tiny local error did not erase the separate destination representation limitation |
| Public reconstruction | Original synthetic corpus, cleaned schema/CLI, C reader harness, safety guard and CI configuration | Public tests are independently reproducible; private aggregate results are not |

The resulting architecture retains exact neutral data while treating transports and engine assets as measured derivatives. The next gate is real engine import/evaluation, with raw/compressed poses and final skinned vertices compared independently. No future feature is presented as completed work.
