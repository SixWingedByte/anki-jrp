# This project is licensed under the terms of the GNU GPL v3: https://www.gnu.org/licenses/
"""Checks that the card script's parsers (src/ts/cards.ts) agree with the Python parsers.

Needs JRP_CARDS_JS (the compiled cards.js from a built package) and node in PATH."""
import json
import os
import shutil
import subprocess
import tempfile
import unittest

from tests.fixtures import INVALID_FIXTURES, PARSE_FIXTURES
from tests.helpers import require

from pylib.segments import parse_jrp, parse_migaku


def python_results(fixtures):
    results = []
    for syntax, value in fixtures:
        try:
            units = (parse_migaku if syntax == "migaku" else parse_jrp)(value)
        except Exception as e:
            results.append({"error": str(e)})
            continue
        results.append({"units": [{
            "text": u.text(),
            "reading": u.reading(),
            "accent_reading": u.accent_reading(),
            "accents": [str(a) for a in u.accents or []],  # parse_migaku leaves None without a tag
            "is_yougen": u.is_yougen,
            "uncertain": u.uncertain,
        } for u in units]})
    return results


class ParityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cards_js = require("JRP_CARDS_JS")["JRP_CARDS_JS"]
        if not shutil.which("node"):
            require("JRP_NODE_MISSING")  # skips, or fails in CI
        fixtures = PARSE_FIXTURES + INVALID_FIXTURES
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as fd:
            json.dump(fixtures, fd, ensure_ascii=False)
        try:
            out = subprocess.run(["node", os.path.join(os.path.dirname(__file__), "parity.js"), cards_js, fd.name],
                                 capture_output=True, check=True)
        finally:
            os.remove(fd.name)
        cls.fixtures = fixtures
        cls.js = json.loads(out.stdout.decode("utf-8"))
        cls.py = python_results(fixtures)

    def test_valid_inputs_agree(self):
        for i, (syntax, value) in enumerate(PARSE_FIXTURES):
            with self.subTest(syntax=syntax, value=value):
                self.assertNotIn("error", self.js[i], f"card script failed: {self.js[i]}")
                self.assertEqual(self.js[i], self.py[i])

    def test_invalid_inputs_rejected(self):
        for i, (syntax, value) in enumerate(INVALID_FIXTURES, len(PARSE_FIXTURES)):
            with self.subTest(syntax=syntax, value=value):
                self.assertIn("error", self.py[i])
                self.assertIn("error", self.js[i], f"card script accepted it: {self.js[i]}")


if __name__ == "__main__":
    unittest.main()
