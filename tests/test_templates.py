# This project is licensed under the terms of the GNU GPL v3: https://www.gnu.org/licenses/
"""Generated note type CSS and card script wrapper (src/ankilib/templates.py)."""
import importlib
import json
import os
import re
import sys
import tempfile
import types
import unittest

from tests.helpers import SRC_DIR


def _load_templates():
    # templates.py only needs Anki for type names; stub them so the module imports without Anki
    for name in ("anki", "anki.collection", "anki.models"):
        sys.modules.setdefault(name, types.ModuleType(name))
    sys.modules["anki.collection"].Collection = object
    sys.modules["anki.models"].NotetypeDict = dict
    pkg = types.ModuleType("jrp_addon")
    pkg.__path__ = [SRC_DIR]
    sys.modules["jrp_addon"] = pkg
    ankilib = types.ModuleType("jrp_addon.ankilib")
    ankilib.__path__ = [os.path.join(SRC_DIR, "ankilib")]
    sys.modules["jrp_addon.ankilib"] = ankilib

    cards_js = tempfile.NamedTemporaryFile("w", suffix=".js", delete=False)
    cards_js.write("generate();\n")
    cards_js.close()
    util = types.ModuleType("jrp_addon.ankilib.util")
    util.get_path = lambda *p: cards_js.name if p[0] == "js" else os.path.join(SRC_DIR, *p)
    sys.modules["jrp_addon.ankilib.util"] = util
    return (importlib.import_module("jrp_addon.ankilib.templates"),
            importlib.import_module("jrp_addon.pylib.preferences").StylePrefs)


templates, StylePrefs = _load_templates()


def specificity(sel: str):
    s = sel.replace(":hover", " .x")
    return (len(re.findall(r"\.[\w-]+|\[[^\]]+\]", s)), len(re.findall(r"(?:^|[\s>+~])([a-z][\w-]*)", s)))


def rules(css: str):
    """(selector, body, rule index) for every selector in the stylesheet."""
    return [(sel.strip(), body.strip(), i)
            for i, (sels, body) in enumerate(re.findall(r"([^{}]+)\{([^{}]*)\}", css))
            for sel in sels.split(",")]


class MigakuStyleTests(unittest.TestCase):
    def test_off_by_default(self):
        css = templates.generate_css(StylePrefs())
        self.assertNotIn(".jrp-graph-labels", css)
        self.assertNotIn("jrp-no-furigana", css)

    def test_enables_diamonds(self):
        css = templates.generate_css(StylePrefs(migaku_style=True))
        self.assertIn(".jrp-indicator-container .jrp-indicator:first-child", css)

    def test_furigana_hover_doesnt_override_front(self):
        r = rules(templates.generate_css(StylePrefs(migaku_style=True)))
        shows = [x for x in r if x[0] in ("[data-jrp-generate] :hover > rt", "[data-jrp-generate] .jrp-revealed rt")]
        fronts = [x for x in r if x[0] in (".jrp-front [data-jrp-generate] rt", ".jrp-front[data-jrp-generate] rt")]
        hidden = [x for x in r if x[0] == "[data-jrp-generate] rt"]
        self.assertTrue(shows and fronts and hidden)
        for show in shows:
            self.assertGreater(specificity(show[0]), specificity(hidden[0][0]))
            for front in fronts:
                # front.css must win: higher specificity, or equal and later
                self.assertTrue(specificity(show[0]) < specificity(front[0])
                                or (specificity(show[0]) == specificity(front[0]) and show[2] < front[2]),
                                f"{show[0]} overrides {front[0]}")

    def test_display_type_rules_win(self):
        self.assertGreater(specificity(".jrp-no-color .jrp-unit[class] > span"),
                           specificity(".jrp-unit.jrp-heiban > span"))
        self.assertGreater(specificity("[data-jrp-generate].jrp-furigana-always rt"),
                           specificity("[data-jrp-generate] rt"))

    def test_script_options(self):
        for on in (False, True):
            js = templates.generate_js(StylePrefs(migaku_style=on), answer_side=True)
            options = json.loads(re.search(r"const jrp_options = (\{[^}]*\});", js).group(1))
            self.assertEqual(options, {"hiragana_graph": on, "migaku_templates": on, "pattern_labels": on})
            self.assertIn("const jrp_answer_side = true;", js)

    def test_toggling_rewrites_script(self):
        nt = {"css": "", "tmpls": [{"qfmt": "Q", "afmt": "A"}]}
        self.assertIsNotNone(templates.update_script(nt, StylePrefs()))
        self.assertIsNone(templates.update_script(nt, StylePrefs()))
        self.assertIsNotNone(templates.update_script(nt, StylePrefs(migaku_style=True)))


class ManagedSectionTests(unittest.TestCase):
    def test_old_numeric_tag_replaced_once(self):
        nt = {"css": "body{}\n\n/* JRP add-on managed section start [version:0] */\nOLD\n"
                     "/* JRP add-on managed section end */", "tmpls": []}
        self.assertIsNotNone(templates.update_style(nt, StylePrefs()))
        self.assertNotIn("OLD", nt["css"])
        self.assertIsNone(templates.update_style(nt, StylePrefs()))
        self.assertIsNotNone(templates.update_style(nt, StylePrefs(atamadaka="red")))
        self.assertEqual(nt["css"].count("managed section start"), 1)


if __name__ == "__main__":
    unittest.main()
