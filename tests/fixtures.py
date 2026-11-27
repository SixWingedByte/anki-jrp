# This project is licensed under the terms of the GNU GPL v3: https://www.gnu.org/licenses/
# Inputs parsed by both the Python parsers (src/pylib/segments.py) and the card script
# (src/ts/cards.ts); see test_parity.py.
PARSE_FIXTURES = [
    ("jrp", "{[辞書|じしょ];1}を{[引|ひ]く;Y0}"),
    ("jrp", "[日本|にほん]の{[受|う]け[入|い]れる;Y4,0}"),
    ("jrp", "{[一目瞭然|いちもくりょうぜん];2@4-0@4,0}"),
    ("jrp", "{[行|い][って=く];Y0}"),
    ("jrp", "{[来|き]た;Y1|くる}"),
    ("jrp", "{[日|ひ];!1}"),
    ("jrp", "{ねこ;1}が{[好|す]き;2}"),
    ("jrp", "ひらがなだけ"),
    ("jrp", "{[日本|にほん];2}&nbsp;です"),
    ("jrp", "{[雨|あめ];1}\xa0の{[日|ひ];1}"),
    ("jrp", "\\{escaped\\} \\[text"),
    ("migaku", "辞書[じしょ;a]"),
    ("migaku", "陥[おとしい,おとしいれる;k5,h]れる"),
    ("migaku", "バナナ[;a]"),
    ("migaku", "日本[にほん] 語[ご]"),
    ("migaku", "見[み;h]る&nbsp;人[ひと;h]"),
    ("migaku", "日本[にほん]の 辞書[じしょ]"),
]

# Inputs that both parsers must reject.
INVALID_FIXTURES = [
    ("jrp", "{[辞書|じしょ];1"),
    ("jrp", "[辞書じしょ]"),
    ("jrp", "{[辞書|じしょ];x}"),
    ("migaku", "辞書[じしょ;a"),
]
