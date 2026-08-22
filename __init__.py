import os
import anki.hooks
import aqt
from aqt.editor import Editor
from aqt.browser import Browser
from aqt.utils import tooltip
from aqt.qt import QMenu
from .editor import EditorDialog
from .dictionary import Dictionary


def import_all_dictionaries() -> None:
    config = aqt.mw.addonManager.getConfig(__name__)
    from .editor.editor import EditorDialog
    for path in config.get("dictionaries", []):
        if Dictionary.validate_file(path) and path not in EditorDialog._dict_cache:
            EditorDialog._dict_cache[path] = Dictionary(path)


def editor_action(browser: Browser, menu: QMenu = None) -> None:
    def open_editor_for_selected_notes(browser: Browser) -> None:
        nids = browser.selectedNotes()
        if nids:
            EditorDialog(browser, nids)
        else:
            tooltip("No cards selected.")

    if menu is None:
        menu = browser.form.menuEdit

    menu.addSeparator()
    menu.addAction(
        "WayDict: Add definition", lambda: open_editor_for_selected_notes(browser)
    )


def editor_button(buttons: list[str], editor: Editor) -> list[str]:
    new_button = editor.addButton(
        os.path.dirname(__file__) + "/graphics/icon.png",
        "WayDict: Add definition",
        EditorDialog,
        tip="Add definition",
    )
    buttons.append(new_button)


# Register action in Anki > browse > editor
anki.hooks.addHook("browser.setupMenus", editor_action)

# Register button in Anki > browse > edit
aqt.gui_hooks.editor_did_init_buttons.append(editor_button)

# Register action in Anki > browse > editor
aqt.gui_hooks.browser_will_show_context_menu.append(editor_action)

# Register hook to auto-populate word when note changes
aqt.gui_hooks.editor_did_load_note.append(EditorDialog.on_note_loaded)

# Pre-import all configured dictionaries on startup
aqt.gui_hooks.profile_did_open.append(import_all_dictionaries)
