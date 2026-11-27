#!/usr/bin/env python3
# This project is licensed under the terms of the GNU GPL v3: https://www.gnu.org/licenses/
"""Builds the add-on's dictionary data (data/accents.xz and data/variants.xz).

- variants.xz: word variants from the current JMdict (src/import_jmdict.py).
- accents.xz: pitch accents from Kanjium, with an existing accents.xz (the data shipped with
  v0.2) as fallback for words Kanjium doesn't have. For a word + reading pair in both, Kanjium
  wins, except where the fallback has a split accent (e.g. 一目瞭然), which Kanjium can't express.

usage: build_data.py <OUTPUT DIR> <JMdict.gz> <Kanjium accents.txt> <fallback accents.xz>
"""
import gzip
import lzma
import os
import re
import subprocess
import sys
from typing import Dict, List, Set, Tuple

SRC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, "src")
sys.path.insert(0, SRC_DIR)

from pylib.accents import Accent  # noqa: E402
from pylib.normalize import to_hiragana  # noqa: E402

KANJIUM_SOURCE = "Ｋ"
_pos_re = re.compile(r"\([^)]*\)")
_jmdict_created_re = re.compile(rb"<!-- JMdict created: ([0-9-]+) -->")

Pair = Tuple[str, str]  # (reading in hiragana, variant)
Value = Tuple[Tuple[str, ...], str]  # (accents, source chars)


def read_fallback(path: str) -> Dict[Pair, Value]:
    pairs: Dict[Pair, Value] = {}
    with lzma.open(path, "rt", encoding="utf-8") as fd:
        for line in fd:
            if line.startswith("#"):
                continue
            reading, variants, accents, sources = line.rstrip("\n").split("\t")
            for variant in variants.split(","):
                pairs[(reading, variant)] = (tuple(accents.split(",")), sources)
    return pairs


def read_kanjium(path: str) -> Dict[Pair, Value]:
    """Kanjium accents.txt: word<TAB>reading (empty for kana-only words)<TAB>accents, where
    accents may carry part-of-speech prefixes like (副)0,(名)3."""
    pairs: Dict[Pair, Value] = {}
    with open(path, encoding="utf-8") as fd:
        for line in fd:
            fields = line.rstrip("\n").split("\t")
            if len(fields) != 3:
                continue
            word, reading, accents = fields
            if not word or "," in word:
                continue
            nums: List[str] = []
            for acc in _pos_re.sub("", accents).split(","):
                acc = acc.strip()
                if acc.isdigit() and acc not in nums:
                    nums.append(str(int(acc)))
            if nums:
                pairs[(to_hiragana(reading or word), word)] = (tuple(nums), KANJIUM_SOURCE)
    return pairs


def merge(kanjium: Dict[Pair, Value], fallback: Dict[Pair, Value]) -> Dict[Pair, Value]:
    merged = dict(fallback)
    for pair, value in kanjium.items():
        old = merged.get(pair)
        if old and any("@" in acc for acc in old[0]):
            continue  # keep split accents
        merged[pair] = value
    return merged


def write_accents(path: str, pairs: Dict[Pair, Value]) -> int:
    # group variants with the same reading and accents into one entry, like the original importer
    groups: Dict[Tuple[str, Tuple[str, ...]], Tuple[Set[str], Set[str]]] = {}
    for (reading, variant), (accents, sources) in pairs.items():
        variants, srcs = groups.setdefault((reading, accents), (set(), set()))
        variants.add(variant)
        srcs.update(sources)

    with lzma.open(path, "wt", encoding="utf-8") as fd:
        fd.write("# pitch accent dictionary; Ｋ: Kanjium (github.com/mifunetoshiro/kanjium, CC BY-SA 4.0); "
                 "other sources taken from the Migaku Japanese add-on\n")
        fd.write("# sources: Ｋ: Kanjium; 日: NHKアクセント 1998版; 林: 大辞林 第二版; Ｍ: manual changes from MIA; "
                 "和: 和独辞典; 新: 新明解 第五版\n")
        fd.write("# format: reading<TAB>variant{,variant}<TAB>accent{,accent}<TAB>source{source}\n")
        for (reading, accents) in sorted(groups):
            variants, srcs = groups[(reading, accents)]
            fd.write(f"{reading}\t{','.join(sorted(variants))}\t{','.join(accents)}\t{''.join(sorted(srcs))}\n")
    return len(groups)


def build_variants(out_path: str, jmdict_path: str) -> Tuple[int, str]:
    with gzip.open(jmdict_path, "rb") as fd:
        m = _jmdict_created_re.search(fd.read(1 << 20))
    created = m.group(1).decode() if m else "unknown"

    tmp_path = out_path + ".tmp"
    subprocess.run([sys.executable, "import_jmdict.py", os.path.abspath(tmp_path), os.path.abspath(jmdict_path)],
                   cwd=SRC_DIR, check=True)
    count = 0
    with lzma.open(tmp_path, "rt", encoding="utf-8") as src, lzma.open(out_path, "wt", encoding="utf-8") as dst:
        dst.write(f"# word variant mapping generated from JMdict (created {created}), "
                  "© EDRDG, CC BY-SA 4.0: https://www.edrdg.org/edrdg/licence.html\n")
        dst.write("# format: reading{,reading}<TAB>variant{,variant}\n")
        for line in src:
            if not line.startswith("#"):
                dst.write(line)
                count += 1
    os.remove(tmp_path)
    return count, created


def validate(accents_path: str, variants_path: str) -> None:
    from pylib.dictionary import AccentEntry, BasicDict, Dictionary, VariantEntry

    for path, fields in ((accents_path, 4), (variants_path, 2)):
        with lzma.open(path, "rt", encoding="utf-8") as fd:
            for n, line in enumerate(fd, 1):
                if not line.startswith("#") and len(line.rstrip("\n").split("\t")) != fields:
                    sys.exit(f"{path}:{n}: expected {fields} fields: {line!r}")

    with lzma.open(accents_path, "rt", encoding="utf-8") as fd:
        for line in fd:
            if not line.startswith("#"):
                for acc in line.split("\t")[2].split(","):
                    Accent.from_str(acc)

    dic = Dictionary(BasicDict(AccentEntry, accents_path), BasicDict(VariantEntry, variants_path))
    expected = {("箸", "はし"): "1", ("橋", "はし"): "2", ("端", "はし"): "0", ("雨", "あめ"): "1",
                ("飴", "あめ"): "0", ("辞書", "じしょ"): "1", ("日本", "にほん"): "2", ("日本", "にっぽん"): "3"}
    for (word, reading), accent in expected.items():
        entries = dic.accent.look_up_variant(word) or []
        found = [",".join(map(str, e.accents)) for e in entries if e.reading == reading]
        if not any(accent in f.split(",") for f in found):
            sys.exit(f"sanity check failed: {word} ({reading}) should have accent {accent}, found {found}")


def main(out_dir: str, jmdict: str, kanjium_path: str, fallback_path: str) -> None:
    os.makedirs(out_dir, exist_ok=True)
    accents_path = os.path.join(out_dir, "accents.xz")
    variants_path = os.path.join(out_dir, "variants.xz")

    fallback = read_fallback(fallback_path)
    kanjium = read_kanjium(kanjium_path)
    merged = merge(kanjium, fallback)
    entries = write_accents(accents_path, merged)
    variant_lines, created = build_variants(variants_path, jmdict)
    validate(accents_path, variants_path)

    only_kanjium = len(kanjium.keys() - fallback.keys())
    changed = sum(1 for p, v in kanjium.items() if p in fallback and fallback[p][0] != v[0] and merged[p] == v)
    print(f"accents: {len(merged)} word+reading pairs in {entries} entries "
          f"({len(fallback)} from fallback, {only_kanjium} added by Kanjium, {changed} changed by Kanjium)")
    print(f"variants: {variant_lines} lines from JMdict created {created}")


if __name__ == "__main__":
    if len(sys.argv) != 5:
        sys.exit(__doc__)
    main(*sys.argv[1:])
