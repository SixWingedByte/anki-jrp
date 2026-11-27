#!/usr/bin/env python3
# This project is licensed under the terms of the GNU GPL v3: https://www.gnu.org/licenses/
"""Extracts the MeCab shared libraries for macOS and Linux from pinned fugashi wheels.

The add-on loads them with ctypes (see src/pylib/mecab.py), so only the library files are
needed, not fugashi itself, and they work with any Python version. Windows uses the
libmecab.dll that's bundled with mecab.exe.

usage: fetch_mecab_libs.py <OUTPUT DIR>
"""
import hashlib
import os
import sys
import urllib.request
import zipfile
from io import BytesIO

_BASE = "https://files.pythonhosted.org/packages"
# fugashi 1.5.2 (MIT), bundling MeCab 0.996 (BSD-3-Clause)
WHEELS = {
    "libmecab-macos.dylib": (
        f"{_BASE}/0b/8d/bfe6958e1afa874c8a2e3016728fb0d69d33c08fd96f27327d8eab8bff6e/"
        "fugashi-1.5.2-cp313-cp313-macosx_10_13_universal2.whl",
        "5cd0a399aad72d00a3b6b2d8c45e43a8c1e3aefd86ba153c826426b8e133e533"),
    "libmecab-linux-x86_64.so": (
        f"{_BASE}/c8/b4/07c38f81d69e02d3edce0fa1de545e12aed3f518e0d9304a7a061dc0b79f/"
        "fugashi-1.5.2-cp313-cp313-manylinux2014_x86_64.manylinux_2_17_x86_64.whl",
        "0e79d3f09d847d07eddf8e62ad9840b11331102bc31ecd66455c62581af11638"),
    "libmecab-linux-aarch64.so": (
        f"{_BASE}/58/6c/827a698ab08b98d221995a44ebec382e5ee4e1bfd4f123ade612ba3b6b04/"
        "fugashi-1.5.2-cp313-cp313-manylinux2014_aarch64.manylinux_2_17_aarch64.whl",
        "32e01a394011270078efb6c71ef188c327255544d953692cd82f7f726d59ecc4"),
}


def fetch(url: str, sha256: str) -> bytes:
    with urllib.request.urlopen(url) as resp:
        data = resp.read()
    digest = hashlib.sha256(data).hexdigest()
    if digest != sha256:
        sys.exit(f"checksum mismatch for {url}: {digest}")
    return data


def main(out_dir: str) -> None:
    os.makedirs(out_dir, exist_ok=True)
    licenses_written = False
    for target, (url, sha256) in WHEELS.items():
        whl = zipfile.ZipFile(BytesIO(fetch(url, sha256)))
        libs = [n for n in whl.namelist() if os.path.basename(n).startswith("libmecab")]
        if len(libs) != 1:
            sys.exit(f"expected one libmecab in {url}, found {libs}")
        with open(os.path.join(out_dir, target), "wb") as fd:
            fd.write(whl.read(libs[0]))
        print(f"{target} <- {libs[0]}")

        if not licenses_written:
            for name in whl.namelist():
                base = os.path.basename(name)
                if ".dist-info/" in name and base.startswith("LICENSE"):
                    out_name = "LICENSE.fugashi" if base == "LICENSE" else base
                    with open(os.path.join(out_dir, out_name), "wb") as fd:
                        fd.write(whl.read(name))
                    print(f"{out_name} <- {name}")
            licenses_written = True

    # MeCab needs a resource file to start; an empty one is enough when the dictionary is given.
    open(os.path.join(out_dir, "mecabrc"), "w").close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
