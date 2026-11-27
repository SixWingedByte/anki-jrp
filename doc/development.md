# Development

## Repository Layout

```text
src/
├── __init__.py      add-on entry point
├── ankilib/         Anki integration: hooks, editor buttons, bulk conversion,
│                    preferences UI, note type script/style management
├── pylib/           everything that doesn't need Anki: MeCab, dictionary,
│                    conversion, syntax parsers and formatters, preferences
├── ts/cards.ts      card script that turns reading/accent syntax into HTML
├── style/           CSS templates for the note type stylesheet
└── assets/          icons and graph images
tools/
├── build_data.py        builds data/accents.xz and data/variants.xz
└── fetch_mecab_libs.py  gets the MeCab libraries for macOS and Linux
tests/               unit, conversion and parser parity tests
make.py              builds the .ankiaddon packages
.github/workflows/build.yml   builds, tests and releases
```

## How the Card Script and Styles Reach Note Types

For each note type added in the preferences, the add-on inserts the compiled
card script into every card template and the generated stylesheet
(`ankilib/templates.py`) into the note type's styling. Both are placed in
sections marked as managed by the add-on. Each section's start marker contains
a hash of its contents, and a section is rewritten whenever newly generated
code hashes differently: when Anki starts after an add-on update, and when the
preferences are saved. The _Update Script_ and _Update Style_ buttons rewrite
them unconditionally.

The script is wrapped in a function that defines two values for it:
`jrp_answer_side` (true in back templates) and `jrp_options` (options from the
note type's style settings, see `script_options` in `templates.py`).

## Building

The [GitHub workflow](#github-workflow) builds everything; doing it locally
needs:

- Python 3.10 or later
- TypeScript 4.9 (`npm install --global typescript@4.9.4`); `make.py` uses its
  `tsc` command-line options
- the data and binaries that aren't in the repository:
  - `data/accents.xz` and `data/variants.xz`: see [Dictionary Data](#dictionary-data)
  - for Windows: `mecab.exe` and `libmecab.dll`
  - the compiled IPAdic dictionary for MeCab
  - the MeCab libraries for macOS and Linux:
    `python tools/fetch_mecab_libs.py <LIB DIR>`

The workflow takes the Windows binaries and IPAdic from the upstream v0.2
release, verified by checksum (see `BUNDLE_*` in the workflow). Then:

```bash
python make.py <DATA DIR> <WINDOWS BIN DIR> <IPADIC DIR> <LIB DIR>
```

The packages are written to `target/`:

| File | Contents |
|---|---|
| `…_<version>_full.ankiaddon` | everything |
| `…_<version>_no-dictionary.ankiaddon` | everything except IPAdic |
| `…_<version>_lite.ankiaddon` | only the add-on code |
| `…_script-only_<version>.zip` | `pylib` only |

The version comes from `src/pylib/version.py`. Don't edit it for releases;
the workflow sets it from the release version.

## Dictionary Data

`tools/build_data.py` builds the two data files:

```bash
python tools/build_data.py <OUTPUT DIR> JMdict.gz kanjium-accents.txt fallback-accents.xz
```

- **Variants** come from JMdict (`src/import_jmdict.py`). EDRDG regenerates
  JMdict daily and doesn't keep old versions, so the workflow always uses the
  current file and logs its checksum and creation date. Downloads are retried
  and tried from both EDRDG hosts (`JMDICT_URLS` in the workflow). If JMdict
  can't be downloaded at all, the workflow passes the `variants.xz` of the
  upstream v0.2 release instead of `JMdict.gz` and shows a warning on the run,
  so the build doesn't depend on EDRDG being reachable.
- **Accents** come from Kanjium's `accents.txt`, pinned to a commit and checked
  by SHA-256 (`KANJIUM_URL` and `KANJIUM_SHA256` in the workflow). Word and
  reading pairs Kanjium doesn't have are taken from the fallback file, the
  `accents.xz` of the upstream v0.2 release. Where both have a pair, Kanjium's
  value is used unless the fallback has a split accent.
- The script checks the format of every line, that every accent parses, and
  the accents of a few known words, and fails if anything is off.

To update Kanjium, change both values in the workflow to a newer commit and
the new file's checksum. Credit for all sources is in the README; keep it up to
date when adding sources.

## MeCab Libraries

`src/pylib/mecab.py` has two backends with the same output:

- `MecabLib` loads the MeCab C library with `ctypes` and runs it in-process.
  It doesn't depend on the Python version. Windows x64 uses the bundled
  `bin/libmecab.dll`; macOS and Linux use the files in `lib/`, which
  `tools/fetch_mecab_libs.py` extracts from pinned [fugashi](https://github.com/polm/fugashi)
  wheels. To update them, change the URLs and checksums in that script.
- `Mecab` runs the MeCab executable as a subprocess. It's the fallback when
  the library isn't available.

`ankilib/global_vars.py` (`init_mecab`) chooses between them. `bin/` is deleted
on macOS and Linux after add-on updates (see `ankilib/updates.py`), so files
that must stay go in `lib/`.

## Tests

```bash
python -m unittest discover -s tests -t . -v
```

- `test_pylib.py`: parsers, formatters, syntax detection, accents.
- `test_templates.py`: generated CSS precedence, card script options, managed
  section updates.
- `test_conversion.py`: end-to-end conversion with the MeCab library and the
  dictionary data. Needs `JRP_DATA_DIR`, `JRP_IPADIC_DIR`, `JRP_MECAB_LIB` (path
  to the library for your platform) and `JRP_MECABRC` (an empty file).
- `test_parity.py`: runs the compiled card script in Node (`parity.js`) and
  checks that its parsers agree with the Python ones on the inputs in
  `fixtures.py`. Needs `node` and `JRP_CARDS_JS` (the `js/cards.js` from a
  built package).

Tests whose requirements are missing are skipped. With `JRP_REQUIRE_ALL=1`, as
in the workflow, they fail instead. When changing a parser, add inputs to
`fixtures.py` so both implementations are checked.

## GitHub Workflow

`.github/workflows/build.yml` runs on pull requests, on version tags and when
started manually. It:

1. builds the dictionary data and gets the MeCab libraries,
2. builds the packages with `make.py` and checks their contents,
3. runs all tests against the built data and the packaged card script,
4. uploads the packages as the `ankiaddon` workflow artifact,
5. for releases only: creates the tag and a draft release with the packages.

## Releasing

1. Go to _Actions_ → _Build add-on_ → _Run workflow_, leave _Use workflow
   from_ on `master` and enter the new version, e.g. `0.4`.
2. The workflow builds version 0.4, runs the tests, tags the commit as `v0.4`
   (only if everything passed) and creates a draft release with the packages.
3. Check the draft under _Releases_ and click _Publish release_.

Pushing a tag from git (`git tag v0.4 && git push origin v0.4`) also creates a
draft release. If a release for the tag already exists, for example because it
was published in the web UI first, the packages are attached to it instead.
