# This project is licensed under the terms of the GNU GPL v3: https://www.gnu.org/licenses/; © 2022 Ben Kerman
import dataclasses
import hashlib
import re
from re import Pattern
from typing import Any, Dict, List, Optional, Tuple

from anki.collection import Collection
from anki.models import NotetypeDict

from .util import get_path
from ..pylib.preferences import AddonPrefs, NoteTypePrefs, StylePrefs


def _read_file(*path_comps: str) -> str:
    with open(get_path(*path_comps), encoding="utf-8") as fd:
        return fd.read()


def _compress_spaces(data: str) -> str:
    return " ".join(line for line in (raw_line.strip() for raw_line in data.splitlines()) if line)


_patterns = ("heiban", "kifuku", "atamadaka", "odaka", "nakadaka")
_patterns_unk = _patterns + ("unknown",)


def _fmt_css(fmt_def: Dict[str, Any]) -> str:
    fmt = _read_file("style", f"{fmt_def['name']}.{fmt_def['type']}")
    if fmt_def["type"] == "var":
        css = fmt.format(**fmt_def["vars"])
    elif fmt_def["type"] == "pat":
        css = "".join(fmt.format(pattern=pat) for pat in fmt_def["pats"])
    else:
        css = fmt
    if fmt_def.get("tap"):
        # same rules for words revealed by tapping (devices without hover, see cards.ts)
        css += css.replace(":hover", ".jrp-revealed")
    return css


def generate_css(prefs: StylePrefs) -> str:
    files = [
        {
            "name": "variables",
            "type": "var",
            "vars": dataclasses.asdict(prefs)
        }, {
            "name": "unit",
            "type": "css"
        }, {
            "name": "pattern",
            "type": "pat",
            "pats": _patterns_unk
        }, {
            "name": "split-accent" if prefs.highlight_split_accents else "split-accent-unknown",
            "type": "pat",
            "pats": _patterns
        }, {
            "name": "indicator-diamond" if prefs.use_diamond_indicators else "indicator-bar",
            "type": "css"
        }, {
            "name": "graph",
            "type": "css"
        }
    ]
    if prefs.hide_on_front:
        files.append({
            "name": "front",
            "type": "css"
        })
        if prefs.hover_front_coloring:
            files.append({"name": "front-hover-color", "type": "css", "tap": True})
            files.append({"name": "front-hover-color", "type": "pat", "pats": _patterns_unk, "tap": True})
            if prefs.highlight_split_accents:
                files.append({"name": "front-hover-split", "type": "pat", "pats": _patterns, "tap": True})
        if prefs.hover_front_graph:
            files.append({"name": "front-hover-graph", "type": "css", "tap": True})
            files.append({"name": "front-hover-graph", "type": "pat", "pats": _patterns_unk, "tap": True})
        if prefs.hover_front_furigana:
            files.append({"name": "front-hover-furigana", "type": "css", "tap": True})
        if prefs.hover_front_indicators:
            files.append({"name": "front-hover-indicators", "type": "var", "tap": True,
                          "vars": {"display": "inline-block" if prefs.use_diamond_indicators else "flex"}})
    if not prefs.graph_particle:
        files.append({
            "name": "graph-no-particle",
            "type": "css"
        })
    return _compress_spaces("".join(_fmt_css(fmt_def) for fmt_def in files))


def generate_js(answer_side: bool = False) -> str:
    side = "true" if answer_side else "false"
    return f"(function(){{ const jrp_answer_side = {side}; {_compress_spaces(_read_file('js', 'cards.js'))} }})();"


_trail_str = "Do Not Edit If Using Automatic CSS and JS Management"
_css_re = re.compile(rf"\n*/\*###((?:MIA|MIGAKU) JAPANESE SUPPORT) CSS STARTS###\n"
                     rf"{_trail_str}\*/.*?/\*###\1 CSS ENDS###\*/\n*", re.S)
_js_re = re.compile(rf"\n*<!--###((?:MIA|MIGAKU) JAPANESE SUPPORT) ((?:(?:KATAKANA )?CONVERTER )?JS) START###\n"
                    rf"{_trail_str}-->.*?<!--###\1 \2 ENDS###-->\n*", re.S)


def remove_mia_migaku(nt: NotetypeDict):
    nt["css"] = _css_re.sub("", nt["css"])
    for tpl in nt["tmpls"]:
        for fmt_name in ("qfmt", "afmt"):
            tpl[fmt_name] = _js_re.sub("", tpl[fmt_name])


_comment_symbols = {
    "html": ("<!--", "-->"),
    "css": ("/*", "*/")
}


def _code_hash(code: str) -> str:
    return hashlib.sha1(code.encode("utf-8")).hexdigest()[:12]


def _enclose_code(code: str, css: bool = False) -> str:
    # The start tag carries a hash of the generated code, so a section is only rewritten when
    # its contents would change (e.g. after an add-on update or a style change).
    oc, cc = _comment_symbols["css" if css else "html"]
    return f"{oc} JRP add-on managed section start [version:{_code_hash(code)}] {cc}\n" \
           f"{oc} Changing the opening and closing tags in any way will break automatic CSS/JS handling.\n" \
           f"{' ' * len(oc)} Any manual changes made within this section will be overwritten. {cc}\n" \
           f"{code}\n" \
           f"{oc} JRP add-on managed section end {cc}"


def _split_managed_section(value: str, new_code: str, css: bool = False,
                           force_update: bool = False) -> Optional[Tuple[str, str]]:
    def tag_re(end: bool = False) -> Pattern:
        oc, cc = [re.escape(c) for c in _comment_symbols["css" if css else "html"]]
        # older versions wrote plain numbers instead of hashes; those never match and get replaced
        tag_pat = "end" if end else r"start \[version:([0-9a-f]+)]"
        return re.compile(rf"^[^\S\r\n]*{oc} JRP add-on managed section {tag_pat} {cc}[^\S\r\n]*$", re.M)

    if start_m := tag_re().search(value):
        if not force_update and start_m.group(1) == _code_hash(new_code):
            return None
        if end_m := tag_re(end=True).search(value, start_m.end()):
            return value[:start_m.start()], value[end_m.end():]

    return f"{value.rstrip()}\n\n", ""


def update_style(nt: NotetypeDict, prefs: StylePrefs, force: bool = False) -> Optional[NotetypeDict]:
    def update_css(css: str) -> Optional[str]:
        code = generate_css(prefs)
        if sects := _split_managed_section(css, code, css=True, force_update=force):
            before, after = sects
            return f"{before}{_enclose_code(code, css=True)}{after}"
        else:
            return None

    new_css = update_css(nt["css"])
    if new_css:
        nt["css"] = new_css
        return nt
    else:
        return None


def update_script(nt: NotetypeDict, force: bool = False) -> Optional[NotetypeDict]:
    def update_js(fmt: str, answer_side: bool) -> Optional[str]:
        code = f"<script>{generate_js(answer_side)}</script>"
        if sects := _split_managed_section(fmt, code, force_update=force):
            before, after = sects
            return f"{before}{_enclose_code(code)}{after}"
        else:
            return None

    had_changes = False
    for tpl in nt["tmpls"]:
        for fmt_name in ("qfmt", "afmt"):
            new_fmt = update_js(tpl[fmt_name], answer_side=fmt_name == "afmt")
            if new_fmt:
                had_changes = True
                tpl[fmt_name] = new_fmt

    return nt if had_changes else None


def update_note_type(nt: NotetypeDict, prefs: NoteTypePrefs,
                     old_prefs: Optional[NoteTypePrefs] = None) -> Optional[NotetypeDict]:
    had_changes = False

    if prefs.manage_style:
        if with_style := update_style(nt, prefs.style):
            had_changes = True
            nt = with_style

    if prefs.manage_script:
        if with_script := update_script(nt):
            had_changes = True
            nt = with_script

    return nt if had_changes else None


def update_all_note_types(col: Collection, prefs: AddonPrefs,
                          old_prefs: Optional[AddonPrefs] = None) -> Optional[List[str]]:
    warnings: List[str] = []
    for nt_prefs in prefs.note_types:
        nt = col.models.get(nt_prefs.nt_id)
        if not nt:
            warnings.append(f"Unknown note type ID: {nt_prefs.nt_id}")
            continue

        old_nt_prefs = old_prefs and next(filter(lambda p: p.nt_id == nt_prefs.nt_id, old_prefs.note_types), None)
        nt = update_note_type(nt, nt_prefs, old_nt_prefs)

        if nt:
            try:
                col.models.update_dict(nt)
            except Exception as e:
                warnings.append(f"Failed to update note type with ID {nt_prefs.nt_id}:\n{e}")
                pass

    return warnings or None
