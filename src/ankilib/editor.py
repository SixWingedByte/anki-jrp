# This project is licensed under the terms of the GNU GPL v3: https://www.gnu.org/licenses/; © 2022 Ben Kerman
import json
from enum import Enum, auto
from typing import Callable, Iterable, List, Optional

import aqt.editor
import aqt.utils
from aqt.editor import Editor
from aqt.operations.note import update_note

from . import global_vars as gv
from .util import get_path
from ..pylib.conv_util import detect_syntax, squash_newlines
from ..pylib.converter import convert
from ..pylib.html_processing import strip_html
from ..pylib.mecab import MecabError
from ..pylib.output import OutputType, fmt_jrp, fmt_migaku, insert_nbsp
from ..pylib.segments import ParsingError, parse_jrp, parse_migaku


class ConversionType(Enum):
    GENERATE = auto()
    READINGS = auto()  # TODO implement
    REMOVE = auto()


def _convert(edit: Editor, conv_type: ConversionType, out_type: Optional[OutputType] = None):
    def gen_lines(val: str) -> Iterable[str]:
        lines = strip_html(val)
        if t := detect_syntax(val):
            parser = parse_migaku if t == OutputType.MIGAKU else parse_jrp
            yield from ("".join(u.text() for u in parser(line)) for line in lines)
        else:
            yield from lines

    def transform(val: Optional[str]) -> Optional[str]:
        if val is None:
            return None

        val = squash_newlines(val)
        if conv_type == ConversionType.REMOVE:
            return insert_nbsp("<br>".join(gen_lines(val)))
        else:
            if not out_type:
                raise ValueError("missing output type")

            if not gv.convert_check():
                return None

            try:
                formatter = fmt_migaku if out_type == OutputType.MIGAKU else fmt_jrp
                parsed_lines = (gv.mecab_handle.analyze(line) for line in gen_lines(val))
                conv_lines = (convert(pline, gv.prefs.convert, gv.dictionary) for pline in parsed_lines)
                return "<br>".join(formatter(s, gv.prefs.output) for s in conv_lines)
            except MecabError as e:
                aqt.utils.showWarning(f"Mecab error: {e}")
                return None
            except ParsingError as e:
                aqt.utils.showWarning(f"Conversion failed. Error: {e}")
                return None

    def update_field_html() -> None:
        if (current_field := edit.currentField) is not None:
            if (new_html := transform(edit.note.fields[current_field])) is not None:
                edit.note.fields[current_field] = new_html
                edit.loadNoteKeepingFocus()

    if _is_new_editor(edit):
        # addButton() of the new editor already saves the note before calling us
        _convert_new_editor(edit, transform)
    else:
        edit.call_after_note_saved(update_field_html)


def _is_new_editor(edit) -> bool:
    # NewEditor (experimental Svelte editor) only exists in newer Anki versions, e.g. 26.09
    new_editor_cls = getattr(aqt.editor, "NewEditor", None)
    return new_editor_cls is not None and isinstance(edit, new_editor_cls)


def _convert_new_editor(edit, transform: Callable[[Optional[str]], Optional[str]]):
    # The new editor doesn't hold a Note object; its state lives in the webview.
    field_idx = edit.currentField if edit.currentField is not None else edit.last_field_index
    if field_idx is None:
        return

    def on_note_info(info) -> None:
        if field_idx >= len(info.fields):
            return
        if (new_html := transform(info.fields[field_idx])) is None:
            return

        if info.id:
            # existing note: update it in the collection (undoable), then redraw the editor
            note = edit.mw.col.get_note(info.id)
            note.fields[field_idx] = new_html
            update_note(parent=edit.widget, note=note) \
                .success(lambda _: edit.reload_note()) \
                .run_in_background()
        else:
            # note that is still being added: push the new value into the webview
            fields = list(info.fields)
            fields[field_idx] = new_html
            names = edit.mw.col.models.field_names(edit.mw.col.models.get(info.mid))
            edit.web.eval(f"setFields({json.dumps(names)}, {json.dumps(fields)}); saveNow(true);")

    edit.get_note_info(on_note_info)


def inject_buttons(buttons: List[str], edit: Editor):
    buttons.append(edit.addButton(
        icon=get_path("assets", "convert.svg"),
        cmd="jrp_generate_default",
        func=lambda e: _convert(e, ConversionType.GENERATE, OutputType.DEFAULT),
        tip="(Re)generate readings and accents with default syntax (F2)",
        keys="F2")
    )
    buttons.append(edit.addButton(
        icon=get_path("assets", "migaku.svg"),
        cmd="jrp_generate_migaku",
        func=lambda e: _convert(e, ConversionType.GENERATE, OutputType.MIGAKU),
        tip="(Re)generate readings and accents with Migaku syntax (Ctrl+F2)",
        keys="Ctrl+F2")
    )
    buttons.append(edit.addButton(
        icon=get_path("assets", "restore.svg"),
        cmd="jrp_remove",
        func=lambda e: _convert(e, ConversionType.REMOVE),
        tip="Restore original text (F4)",
        keys="F4")
    )
