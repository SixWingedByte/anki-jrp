# This project is licensed under the terms of the GNU GPL v3: https://www.gnu.org/licenses/; © 2022 Ben Kerman
from typing import List

from anki.collection import Collection
from anki.decks import DeckId
from anki.notes import Note

from . import global_vars as gv
from ..pylib.conv_util import detect_syntax, squash_newlines
from ..pylib.converter import convert
from ..pylib.html_processing import strip_html
from ..pylib.output import fmt_jrp


def field_names(setting: str) -> List[str]:
    return [name.strip() for name in setting.split(",") if name.strip()]


def generate_field(value: str) -> str:
    lines = strip_html(squash_newlines(value))
    return "<br>".join(fmt_jrp(convert(gv.mecab_handle.analyze(line), gv.prefs.convert, gv.dictionary),
                               gv.prefs.output) for line in lines)


def on_note_will_be_added(col: Collection, note: Note, deck_id: DeckId) -> None:
    """Generates readings and accents for the configured fields of new notes.

    Runs for notes added through the Add screen and through add-ons such as AnkiConnect.
    Adding a note never fails because of this: on any problem the field is left as it is."""
    if gv.prefs is None:
        return
    nt_prefs = next((p for p in gv.prefs.addon.note_types if p.nt_id == note.mid), None)
    if nt_prefs is None or not (names := field_names(nt_prefs.auto_generate_fields)):
        return
    if gv.dictionary is None or gv.mecab_handle is None:
        print("JRP: dictionary or MeCab not loaded yet, not generating fields for new note")
        return
    if problem := gv.mecab_problem():
        print(f"JRP: not generating fields for new note: {problem}")
        return

    for name in names:
        if name not in note:
            continue
        value = note[name]
        if not value.strip() or detect_syntax(value):
            continue
        try:
            note[name] = generate_field(value)
        except Exception as e:
            print(f"JRP: generating field {name!r} of new note failed: {e}")
