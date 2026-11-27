# This project is licensed under the terms of the GNU GPL v3: https://www.gnu.org/licenses/
"""End-to-end conversion with the in-process MeCab library and the dictionary data.

Needs JRP_DATA_DIR (accents.xz, variants.xz), JRP_IPADIC_DIR, JRP_MECAB_LIB (shared library)
and JRP_MECABRC (empty resource file)."""
import unittest

from tests.helpers import require

from pylib.converter import convert
from pylib.dictionary import AccentEntry, BasicDict, Dictionary, VariantEntry
from pylib.mecab import MecabLib, MecabUnit
from pylib.output import fmt_anki, fmt_jrp
from pylib.preferences import Prefs


class ConversionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        env = require("JRP_DATA_DIR", "JRP_IPADIC_DIR", "JRP_MECAB_LIB", "JRP_MECABRC")
        cls.mecab = MecabLib(env["JRP_MECAB_LIB"], env["JRP_IPADIC_DIR"], env["JRP_MECABRC"])
        data = env["JRP_DATA_DIR"]
        cls.dic = Dictionary(BasicDict(AccentEntry, f"{data}/accents.xz"),
                             BasicDict(VariantEntry, f"{data}/variants.xz"))
        cls.prefs = Prefs()

    def conv(self, text: str):
        return convert(self.mecab.analyze(text), self.prefs.convert, self.dic)

    def test_mecab_units(self):
        units = self.mecab.analyze("  今日は良い天気")
        self.assertEqual(units[0].value, "  ")  # leading whitespace is kept
        self.assertIsInstance(units[1], MecabUnit)
        self.assertEqual((units[1].value, units[1].reading), ("今日", "きょう"))
        self.assertEqual("".join(u.value for u in units), "  今日は良い天気")

    def test_unknown_word(self):
        self.assertEqual(self.mecab.analyze("ｘｙｚ")[0].hinsi, "未知語")

    def test_default_syntax(self):
        self.assertEqual(fmt_jrp(self.conv("辞書を引く"), self.prefs.output), "{[辞書|じしょ];1}を{[引|ひ]く;Y0}")
        self.assertEqual(fmt_jrp(self.conv("箸と橋"), self.prefs.output), "{[箸|はし];1}と{[橋|はし];2}")

    def test_anki_syntax(self):
        self.assertEqual(fmt_anki(self.conv("辞書を引く")), "辞書[じしょ]を 引[ひ]く")

    def test_many_calls(self):
        for _ in range(500):
            self.mecab.analyze("日本語を勉強しています")


if __name__ == "__main__":
    unittest.main()
