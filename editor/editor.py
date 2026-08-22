import aqt
import aqt.qt
from anki.notes import Note
from anki.collection import Collection
from aqt import mw
from aqt.browser import Browser
from aqt.editor import Editor
from aqt.operations import CollectionOp, QueryOp
from aqt.operations.note import OpChangesWithCount
from aqt.qt import QDialog, QFileDialog, QComboBox, QRadioButton
from aqt.utils import tooltip
from bs4 import BeautifulSoup
from typing import Union
from ..dictionary import Dictionary
from . import form as form


class EditorDialog(QDialog):
    _active_instance: Union["EditorDialog", None] = None
    _dict_cache: dict[str, Dictionary] = {}

    def __init__(
        self,
        context: Union[Editor, Browser],
        nids: list[int] = None,
    ) -> None:
        if nids is None:
            self.editor = context
            self.browser = None
            self.parent_window = self.editor.parentWindow
            self.note = self.editor.note
        else:
            self.editor = None
            self.browser = context
            self.parent_window = self.browser
            self.nids = nids

        QDialog.__init__(self, self.parent_window)
        EditorDialog._active_instance = self
        self.form = form.Ui_Dialog()
        self.form.setupUi(self)
        self.show()
        self.config = mw.addonManager.getConfig(__name__)
        self._migrate_config()
        self.dictionary = None

        note_types = [note_type.name for note_type in mw.col.models.all_names_and_ids()]
        self.form.note_type.addItems(note_types)
        self.form.text_format.addItems(["HTML-Full", "HTML-Brief", "Plain-Text"])

        self._populate_dictionary_combo()
        self.update_definition_view("")
        self.update_combo(self.form.text_format, self.config["text_format"])
        self.update_combo(self.form.note_type, self.config["note_type"])
        self.update_field_items()
        self.update_combo(self.form.source_field, self.config["source_field"])
        self.update_combo(self.form.destination_field, self.config["destination_field"])
        self.form.overwrite_destination.setChecked(self.config["overwrite_destination"])
        self._load_selected_dictionary()

        self._last_searched_word = ""
        self._suppress_dict_save = False

        self.form.text_format.currentIndexChanged.connect(self.on_text_format_change)
        self.form.browse.clicked.connect(self.on_browse)
        self.form.dict_prev.clicked.connect(self.on_dict_prev)
        self.form.dict_next.clicked.connect(self.on_dict_next)
        self.form.search.clicked.connect(self.on_search)
        self.form.start.clicked.connect(self.on_start)

        self.form.dictionary.currentIndexChanged.connect(
            self.on_dictionary_changed
        )
        self.form.note_type.currentIndexChanged.connect(self.update_field_items)
        self.form.note_type.currentIndexChanged.connect(
            lambda: self.on_combo_change(self.form.note_type)
        )
        self.form.source_field.currentIndexChanged.connect(
            lambda: self.on_combo_change(self.form.source_field)
        )
        self.form.destination_field.currentIndexChanged.connect(
            lambda: self.on_combo_change(self.form.destination_field)
        )
        self.form.overwrite_destination.stateChanged.connect(
            lambda: self.on_radio_change(self.form.overwrite_destination)
        )

    def _migrate_config(self) -> None:
        old_path = self.config.get("dictionary_path")
        if old_path and not self.config.get("dictionaries"):
            self.config["dictionaries"] = [old_path]
            self.config["selected_dictionary"] = 0
            del self.config["dictionary_path"]
            self.save_config()

    def _populate_dictionary_combo(self) -> None:
        self.form.dictionary.blockSignals(True)
        self.form.dictionary.clear()
        for path in self.config["dictionaries"]:
            if Dictionary.validate_file(path):
                title = Dictionary.fetch_title(path)
            else:
                title = path.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
            self.form.dictionary.addItem(title, path)
        selected = self.config.get("selected_dictionary", 0)
        if 0 <= selected < self.form.dictionary.count():
            self.form.dictionary.setCurrentIndex(selected)
        self.form.dictionary.blockSignals(False)

    def _current_dict_path(self) -> Union[str, None]:
        idx = self.form.dictionary.currentIndex()
        if idx < 0 or idx >= len(self.config["dictionaries"]):
            return None
        return self.config["dictionaries"][idx]

    def _load_selected_dictionary(self) -> Union[bool, None]:
        path = self._current_dict_path()
        if not path:
            self.dictionary = None
            return False
        if path in self._dict_cache:
            self.dictionary = self._dict_cache[path]
            return True
        if Dictionary.validate_file(path):
            self.import_dictionary(path)
            return None
        else:
            self.dictionary = None
            return False

    def on_dictionary_changed(self) -> None:
        idx = self.form.dictionary.currentIndex()
        if idx < 0:
            return
        if not self._suppress_dict_save:
            self.config["selected_dictionary"] = idx
        loaded = self._load_selected_dictionary()
        word = self.form.word.text()
        if word and loaded is True:
            self.on_search()

    def on_dict_prev(self) -> None:
        count = self.form.dictionary.count()
        if count == 0:
            return
        idx = (self.form.dictionary.currentIndex() - 1) % count
        self.form.dictionary.setCurrentIndex(idx)

    def on_dict_next(self) -> None:
        count = self.form.dictionary.count()
        if count == 0:
            return
        idx = (self.form.dictionary.currentIndex() + 1) % count
        self.form.dictionary.setCurrentIndex(idx)

    def _default_dict_index(self) -> int:
        default_path = self.config.get("default_dictionary")
        if default_path and default_path in self.config["dictionaries"]:
            return self.config["dictionaries"].index(default_path)
        return 0

    def update_combo(self, combo: QComboBox, value: str) -> None:
        if value not in [combo.itemText(i) for i in range(combo.count())]:
            value = combo.itemText(0)
        combo.setCurrentText(value)

    def update_field_items(self) -> None:
        note_type = self.form.note_type.currentText()
        note_type = mw.col.models.by_name(note_type)
        field_names = mw.col.models.field_names(note_type)

        self.form.source_field.clear()
        self.form.destination_field.clear()

        self.form.source_field.addItems(field_names)
        self.form.destination_field.addItems(field_names)

    def update_definition_view(self, definition: str) -> None:
        self.update_definition_preview(definition)
        self.update_definition_source(definition)

    def update_definition_preview(self, text: str) -> None:
        self.form.definition_preview.update_html(text)

    def update_definition_source(self, text: str) -> None:
        if "HTML" in self.config["text_format"]:
            text = BeautifulSoup(text, "html.parser").prettify()
        self.form.definition_source.setPlainText(text)

    def import_dictionary(self, path: str) -> None:
        def save(path: str):
            self.dictionary = Dictionary(path)
            self._dict_cache[path] = self.dictionary

        QueryOp(
            op=lambda col: save(path),
            success=lambda _: _,
            parent=self.parent_window,
        ).with_progress("Importing dictionary...").run_in_background()

    def on_text_format_change(self) -> None:
        self.config["text_format"] = self.form.text_format.currentText()
        self.on_search()

    def on_combo_change(self, combo: QComboBox) -> None:
        self.config[combo.objectName()] = combo.currentText()

    def on_radio_change(self, radio: QRadioButton) -> None:
        self.config[radio.objectName()] = radio.isChecked()

    def on_browse(self) -> None:
        path = QFileDialog.getOpenFileName(
            self, "Open the dictionary", "", "ZIP Files (*.zip)"
        )[0]

        if not path:
            return

        if not Dictionary.validate_file(path):
            tooltip("Select a valid dictionary file.", parent=self.parent_window)
            return

        if path in self.config["dictionaries"]:
            idx = self.config["dictionaries"].index(path)
            self.form.dictionary.setCurrentIndex(idx)
            return

        title = Dictionary.fetch_title(path)
        self.config["dictionaries"].append(path)
        self.form.dictionary.blockSignals(True)
        self.form.dictionary.addItem(title, path)
        self.form.dictionary.setCurrentIndex(self.form.dictionary.count() - 1)
        self.form.dictionary.blockSignals(False)
        self.config["selected_dictionary"] = self.form.dictionary.currentIndex()
        self.save_config()
        self.import_dictionary(path)

    def on_search(self) -> None:
        word = self.form.word.text()

        if not word:
            return

        if word != self._last_searched_word:
            self._last_searched_word = word
            default_idx = self._default_dict_index()
            if self.form.dictionary.currentIndex() != default_idx:
                self._suppress_dict_save = True
                self.form.dictionary.setCurrentIndex(default_idx)
                self._suppress_dict_save = False
                return

        if self.dictionary is None:
            path = self._current_dict_path()
            if path and Dictionary.validate_file(path):
                self.import_dictionary(path)
            else:
                tooltip("Select a valid dictionary file.", parent=self.parent_window)
                return

        def lookup_definition(word: str) -> str:
            definition = self.dictionary.find_definition(word, self.config["text_format"])
            return definition if definition else f"No entries found for '{word}'."

        QueryOp(
            op=lambda _: lookup_definition(word),
            success=lambda definition: self.update_definition_view(definition),
            parent=self.parent_window,
        ).run_in_background()

    def on_start(self) -> None:
        def op(col: Collection) -> OpChangesWithCount:
            if self.editor is not None:
                note = add_note_definition(self.editor.note, self.dictionary)

                if note is None:
                    return OpChangesWithCount(changes=None, count=0)

                return OpChangesWithCount(changes=col.update_note(note), count=1)
            else:
                notes = bulk_add_note_definition(self.nids, self.dictionary)
                return OpChangesWithCount(
                    changes=col.update_notes(notes), count=len(notes)
                )

        def on_success(changes: OpChangesWithCount) -> None:
            tooltip(f"Updated {changes.count} notes.", parent=self.parent_window)

        self.save_config()
        if self.dictionary is None:
            path = self._current_dict_path()
            if path and Dictionary.validate_file(path):
                self.import_dictionary(path)
            else:
                tooltip("Select a valid dictionary file.", parent=self.parent_window)
                return

        CollectionOp(self.parent_window, op).success(on_success).run_in_background()
        self.close()

    def save_config(self) -> None:
        mw.addonManager.writeConfig(__name__, self.config)


def bulk_add_note_definition(nids: list[int], dictionary: Dictionary) -> list[Note]:
    note_list = []
    for i, note_id in enumerate(nids, 1):
        note = mw.col.get_note(note_id)
        note = add_note_definition(note, dictionary)

        if isinstance(note, Note):
            note_list.append(note)

        aqt.mw.taskman.run_on_main(
            lambda: aqt.mw.progress.update(
                label=f"Fetching definitions: {i}/{len(nids)}",
                value=i,
                max=len(nids),
            )
        )
    return note_list


def add_note_definition(note: Note, dictionary: Dictionary) -> Union[Note, None]:
    config = mw.addonManager.getConfig(__name__)

    if not validate_update(note, config):
        return None

    definition = dictionary.find_definition(
        note[config["source_field"]], config["text_format"]
    )

    if not definition:
        return None

    note[config["destination_field"]] = definition

    return note


def validate_update(note: Note, config: dict) -> bool:
    note_type = mw.col.models.get(note.note_type()["id"])["name"]
    note_fields = mw.col.models.field_names(note.note_type())

    if config["note_type"] != note_type:
        return False
    if config["source_field"] not in note_fields:
        return False
    if config["destination_field"] not in note_fields:
        return False
    if note[config["destination_field"]] != "" and not config["overwrite_destination"]:
        return False

    return True
