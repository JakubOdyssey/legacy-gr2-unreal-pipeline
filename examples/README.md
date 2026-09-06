# Original examples

The sole full asset example is [synthetic_asset/neutral.json](synthetic_asset/neutral.json), produced by [tests/synthetic/generate.py](../tests/synthetic/generate.py). It contains no imported geometry, textures, rig names, keys or values taken from a game.

Regenerate with `python -B -m tests.synthetic.generate`; verify with `python -B -m tests.synthetic.generate --check`. Use the README CLI commands to write derivatives into ignored `.local/` storage. Generated FBX/readback files are deliberately not committed, including synthetic ones, so the repository's extension guard stays simple and strict.

The example and its generator are original project material under the repository MIT license. Do not replace them with a proprietary asset to reproduce a bug.
