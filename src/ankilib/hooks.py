# This project is licensed under the terms of the GNU GPL v3: https://www.gnu.org/licenses/; © 2022 Ben Kerman
import anki.hooks
import aqt

from . import auto_generate, browser, editor, global_vars, main_menu, updates

updates.update()

aqt.gui_hooks.collection_did_load.append(global_vars.load_prefs)
aqt.gui_hooks.collection_did_load.append(updates.update_collection)
aqt.gui_hooks.main_window_did_init.append(main_menu.insert_menu_items)
aqt.gui_hooks.editor_did_init_buttons.append(editor.inject_buttons)
aqt.gui_hooks.browser_menus_did_init.append(browser.insert_menu_items)
anki.hooks.note_will_be_added.append(auto_generate.on_note_will_be_added)
