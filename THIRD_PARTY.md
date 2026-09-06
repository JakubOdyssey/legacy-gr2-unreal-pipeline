# Third-party dependency review

Reviewed for this public preparation on 2026-09-06. No third-party source is vendored and no third-party executable is committed. Version references and source-file hashes below identify public upstream material, never the private game corpus.

| Project | Pin | Checked license | Integration / notice handling |
| --- | --- | --- | --- |
| [Rasetsuu/blendergranny](https://github.com/Rasetsuu/blendergranny) | `79b1963ef33df51767cd9ddfd6092846318935ef` | MIT; copyright 2026 ciupix and contributors | Private research decoder lineage only; no source, adapter or binary in this release. Any future copied substantial source requires its full notice and a fresh code/provenance review. |
| [ufbx](https://github.com/ufbx/ufbx) | `fcc5d6ba444cfd3eb80677dba5e37e493941abe5` | MIT alternative selected; copyright 2020 Samuli Raivio | Optional/public CI independent reader. Three explicitly named public files are hash-checked by `tools/build_reader.py`; license retained next to downloaded source. Locally compiled, not a prebuilt download. |
| [jsonschema](https://pypi.org/project/jsonschema/4.26.0/) | 4.26.0 | MIT; Julian Berman | Schema validation dependency, installed from PyPI; bundled COPYING reviewed. No optional format extras. |
| [attrs](https://pypi.org/project/attrs/26.1.0/) | 26.1.0 | MIT; Hynek Schlawack and contributors | Transitive dependency; installed package LICENSE reviewed. |
| [jsonschema-specifications](https://pypi.org/project/jsonschema-specifications/2025.9.1/) | 2025.9.1 | MIT; Julian Berman | Transitive schema resources; installed COPYING reviewed. |
| [referencing](https://pypi.org/project/referencing/0.37.0/) | 0.37.0 | MIT; Julian Berman | Transitive dependency; installed COPYING reviewed. |
| [rpds-py](https://pypi.org/project/rpds-py/2026.6.3/) | 2026.6.3 | MIT; Julian Berman | Transitive dependency with native wheels; PyPI metadata and installed LICENSE reviewed. No wheel/native library vendored here. |

Primary license evidence: [pinned reader license](https://github.com/Rasetsuu/blendergranny/blob/79b1963ef33df51767cd9ddfd6092846318935ef/LICENSE), [pinned ufbx license](https://github.com/ufbx/ufbx/blob/fcc5d6ba444cfd3eb80677dba5e37e493941abe5/LICENSE). Upstream license statements do not constitute clearance for game assets or a complete independent provenance audit. No incompatible implementation was copied.

Python 3.13+ is the supported public baseline. `requirements-dev.txt` pins the complete required Python package set for that baseline. These are version pins, not a hash-locked dependency supply chain. PyPI/network access is required on first installation; use a reviewed offline package mirror if necessary. Compiler, CMake, Python and Git are user-provided tools and are not redistributed.

CI uses commit-pinned official `actions/checkout` and `actions/setup-python` actions (both MIT-licensed upstream projects). Their source is referenced by workflow, not copied. Updating those pins requires review. The workflow has read-only repository permissions and requires no project secrets.

Neither the Granny SDK/runtime nor Unreal Engine is a dependency of this public release or its CI. Adding either changes the dependency and publication review scope.
