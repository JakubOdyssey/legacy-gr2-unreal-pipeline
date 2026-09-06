# Security and publication safety

This is research tooling, not a hardened service for hostile files. Parse only inputs you are authorized to use, inside an isolated process with resource limits. The public CLI reads neutral JSON; it does not open GR2 packages. The C reader disables external-file loading and uses a pinned source revision, but is not an operating-system sandbox.

Never attach game assets, proprietary source, credentials, private paths or complete animation dumps to issues or pull requests. Reproduce bugs with the synthetic generator or a small original fixture whose authorship and license are explicit.

For a suspected vulnerability, use GitHub private vulnerability reporting if the repository owner has enabled it. Do not publish exploit secrets or private asset data in an issue. No private reporting channel is claimed to be configured before publication.

Run `python -B tools/publication_guard.py` in a clean workspace, and `python -B tools/publication_guard.py --staged` before every publication commit. The workspace scan intentionally does not trust `.gitignore` and includes ignored content; remove local build environments/caches or scan a clean checkout. Only the intended root Git metadata is excluded. The index scan reads actual staged blobs, not potentially different working-tree files.

The guard rejects prohibited asset/binary extensions, nested repositories, symlinks, private directories, machine paths, likely credentials/addresses, unexplained long hashes and unapproved neutral payloads. The one full fixture must match its committed generator. Use `--deny-term` for additional private names during a local release review; do not store those names in this repository.

Pattern scanning cannot determine copyright ownership, discover every secret, or recognize arbitrary proprietary snippets. Manual source/provenance review and synthetic reproducibility remain required. A green guard result is a technical publication check, not legal clearance for external data.
