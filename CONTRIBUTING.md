# Contributing

Keep changes small enough to trace from an explicit representation decision to a numerical test. A successful export is not a fidelity result.

Use Python 3.13+ in an isolated environment and install `requirements-dev.txt`. Run `python -B -m unittest discover -s tests/unit -v`. The independent round-trip test skips unless `UFBX_AUDIT` points to a locally built reader; set `REQUIRE_UFBX=1` when validating a release so a missing reader becomes a failure. CI requires that integration test.

Generate fixtures with `python -B -m tests.synthetic.generate`; verify committed bytes with `--check`. Never edit generated data to make a test pass. Changes to the schema must include semantic validation, negative tests and a version/migration decision. Preserve explicit unsupported/default markers; do not silently fill absent animation data.

Add only original synthetic fixtures or clearly licensed public fixtures whose license has been reviewed. Do not submit extracted game data, proprietary source quotations, screenshots/textures or binaries. Keep third-party code unvendored where practical. Document upstream pins and retain required notices for any permitted future copying.

Before committing, review the diff and run the publication guard against the full index. A release review also scans a clean complete workspace. Explain coordinate conventions, numeric precision, sampling schedules, thresholds and observed failure cases in the pull request. Label future Unreal work as unverified until actual engine data has been compared.
