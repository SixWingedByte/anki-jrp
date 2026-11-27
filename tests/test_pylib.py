# This project is licensed under the terms of the GNU GPL v3: https://www.gnu.org/licenses/
import unittest

from tests import helpers  # noqa: F401  (sets up sys.path)
from tests.fixtures import INVALID_FIXTURES, PARSE_FIXTURES

from pylib.accents import Accent
from pylib.conv_util import detect_syntax
from pylib.normalize import split_moras, to_hiragana
from pylib.output import OutputType, fmt_anki, fmt_jrp, fmt_migaku
from pylib.segments import ParsingError, parse_jrp, parse_migaku


def text(units) -> str:
    return "".join(u.text() for u in units)


class ParserTests(unittest.TestCase):
    def test_jrp_round_trip(self):
        for src in ["{[辞書|じしょ];1}を{[引|ひ]く;Y0}", "[日本|にほん]の{[受|う]け[入|い]れる;Y4,0}",
                    "{[一目瞭然|いちもくりょうぜん];2@4-0@4,0}", "{[行|い][って=く];Y0}",
                    "{[来|き]た;Y1|くる}", "{[日|ひ];!1}"]:
            with self.subTest(src=src):
                self.assertEqual(fmt_jrp(parse_jrp(src)), src)

    def test_jrp_units(self):
        units = parse_jrp("{[辞書|じしょ];1}を{[引|ひ]く;Y0}")
        self.assertEqual([u.text() for u in units], ["辞書", "を", "引く"])
        self.assertEqual([[str(a) for a in u.accents] for u in units], [["1"], [], ["0"]])
        self.assertTrue(units[2].is_yougen)
        self.assertEqual(units[2].reading(), "ひく")

    def test_uncertain_and_special_base(self):
        self.assertTrue(parse_jrp("{[日|ひ];!1}")[0].uncertain)
        self.assertEqual(parse_jrp("{[来|き]た;Y1|くる}")[0].accent_reading(), "くる")

    def test_migaku(self):
        units = parse_migaku("陥[おとしい,おとしいれる;k5,h]れる")
        self.assertEqual(text(units), "陥れる")
        self.assertEqual([str(a) for a in units[0].accents], ["5", "0"])
        self.assertEqual([str(a) for a in parse_migaku("辞書[じしょ;a]")[0].accents], ["1"])

    def test_nbsp_is_space(self):
        self.assertEqual(text(parse_jrp("{[日本|にほん];2}&nbsp;です")), "日本 です")
        self.assertEqual(text(parse_jrp("a\xa0b\xa0c")), "a b c")

    def test_invalid(self):
        for syntax, src in INVALID_FIXTURES:
            with self.subTest(src=src):
                with self.assertRaises((ParsingError, ValueError)):
                    (parse_migaku if syntax == "migaku" else parse_jrp)(src)

    def test_all_fixtures_parse(self):
        for syntax, src in PARSE_FIXTURES:
            with self.subTest(src=src):
                (parse_migaku if syntax == "migaku" else parse_jrp)(src)


class OutputTests(unittest.TestCase):
    def test_anki_furigana(self):
        self.assertEqual(fmt_anki(parse_jrp("{[辞書|じしょ];1}を{[引|ひ]く;Y0}")), "辞書[じしょ]を 引[ひ]く")
        self.assertEqual(fmt_anki(parse_jrp("[日本|にほん]の{[受|う]け[入|い]れる;Y4,0}")),
                         "日本[にほん]の 受[う]け 入[い]れる")
        self.assertEqual(fmt_anki(parse_jrp("{[行|い][って=く];Y0}")), "行[い]って")
        self.assertEqual(fmt_anki(parse_jrp("ひらがなだけ")), "ひらがなだけ")

    def test_anki_furigana_restores(self):
        anki = fmt_anki(parse_jrp("{[辞書|じしょ];1}を{[引|ひ]く;Y0}"))
        self.assertEqual(detect_syntax(anki), OutputType.MIGAKU)
        self.assertEqual(text(parse_migaku(anki)), "辞書を引く")

    def test_migaku_output(self):
        self.assertEqual(fmt_migaku(parse_jrp("{[辞書|じしょ];1}")), "辞書[じしょ;a]")

    def test_detect_syntax(self):
        self.assertEqual(detect_syntax("{[辞書|じしょ];1}"), OutputType.DEFAULT)
        self.assertEqual(detect_syntax("[辞書|じしょ]"), OutputType.DEFAULT)
        self.assertEqual(detect_syntax("辞書[じしょ;a]"), OutputType.MIGAKU)
        self.assertIsNone(detect_syntax("辞書を引く"))


class AccentTests(unittest.TestCase):
    def test_from_str(self):
        self.assertEqual(str(Accent.from_str("0")), "0")
        self.assertEqual(str(Accent.from_str("2@4-0@4")), "2@4-0@4")
        self.assertEqual(str(Accent.from_str("2@4-0", 8)), "2@4-0@4")
        self.assertEqual(str(Accent.from_str("?")), "?")

    def test_moras(self):
        self.assertEqual(split_moras("きょう"), ["キョ", "ウ"])
        self.assertEqual(len(split_moras("にっぽん")), 4)
        self.assertEqual(to_hiragana("ニホン"), "にほん")


if __name__ == "__main__":
    unittest.main()
