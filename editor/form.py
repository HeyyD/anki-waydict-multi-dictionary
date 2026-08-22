from aqt.qt import (
    Qt,
    QCoreApplication,
    QMetaObject,
    QUrl,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QGroupBox,
    QWidget,
    QLabel,
    QCheckBox,
    QComboBox,
    QPushButton,
    QLineEdit,
    QTextEdit,
    QTabWidget,
    QWebEngineView,
    QWebEngineSettings,
    QStyle,
)
from aqt import mw
from aqt.theme import colors
from aqt.theme import theme_manager as tm


class DefinitionWebView(QWebEngineView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style = self._get_style()
        self.update_html("")

    def update_html(self, body):
        if not body:
            placeholder = """
                The definition of the word should appear here
                after pressing the "search" button.
            """
            body = f'<span class="placeholder">{placeholder}</span>'

        self.setHtml(
            f"<html><head>{self.style}</head>{body}</html>",
            QUrl(f"{mw.serverURL()}_anki/waydict?id={id(self)}"),
        )

    def _get_style(self):
        font_size, font_style, font_color = self._get_font_style()
        return f"""
            <style>
                body {{
                    background-color: {tm.var(colors.CANVAS)};
                    color: {font_color};
                    font-size: {font_size}pt;
                    font-family: {font_style};
                    overflow-y: scroll;
                    margin: 0;
                    border: 0;
                    padding: 0.7em;
                }}
                ol {{
                    margin: 0;
                    border: 0;
                    padding: 0 0 0 1em;
                }}
                ul {{
                    margin: 0;
                    border: 0;
                    padding: 0 0 0 3em;
                }}
                .placeholder {{
                    color: {tm.var(colors.FG_SUBTLE)};
                }}
                ::-webkit-scrollbar {{
                    width: 12vmin;
                    background-color: transparent;
                }}
                ::-webkit-scrollbar-track {{
                    background-color: transparent;
                }}
                ::-webkit-scrollbar-thumb {{
                    border-color: transparent;
                    border-style: solid;
                    border-width: 2vmin;
                    border-radius: 15px;
                    background-color: {tm.var(colors.SCROLLBAR_BG)};
                    background-clip: padding-box;
                }}
                ::-webkit-scrollbar-thumb:hover {{
                    background-color: {tm.var(colors.SCROLLBAR_BG_HOVER)};
                }}
                ::-webkit-scrollbar-thumb:active {{
                    background-color: {tm.var(colors.SCROLLBAR_BG_ACTIVE)};
                }}
            </style>
        """

    def _get_font_style(self):
        pallete = QTextEdit().palette()
        foreground = QTextEdit().foregroundRole()

        font = QTextEdit().font()
        font_size = font.pointSize()
        font_style = font.family()
        font_color = pallete.color(foreground).name()

        return font_size, font_style, font_color


class Ui_Dialog(object):
    def setupUi(self, Dialog: QWidget):
        Dialog.setObjectName("Dialog")
        Dialog.setMinimumSize(461, 481)
        Dialog.setLayoutDirection(Qt.LayoutDirection.LeftToRight)

        main_layout = QVBoxLayout(Dialog)

        self.dict_group = QGroupBox(parent=Dialog)
        self.dict_group.setObjectName("dict_group")
        dict_layout = QVBoxLayout(self.dict_group)

        dict_buttons_row = QHBoxLayout()
        self.dictionary = QComboBox(parent=self.dict_group)
        self.dictionary.setObjectName("dictionary")
        self.dictionary.setSizePolicy(
            self.dictionary.sizePolicy().horizontalPolicy(),
            self.dictionary.sizePolicy().verticalPolicy(),
        )
        dict_buttons_row.addWidget(self.dictionary, 1)

        self.dict_prev = QPushButton(parent=self.dict_group)
        self.dict_prev.setObjectName("dict_prev")
        self.dict_prev.setIcon(self.dict_prev.style().standardIcon(QStyle.StandardPixmap.SP_ArrowLeft))
        self.dict_prev.setFixedWidth(28)
        dict_buttons_row.addWidget(self.dict_prev)

        self.dict_next = QPushButton(parent=self.dict_group)
        self.dict_next.setObjectName("dict_next")
        self.dict_next.setIcon(self.dict_next.style().standardIcon(QStyle.StandardPixmap.SP_ArrowRight))
        self.dict_next.setFixedWidth(28)
        dict_buttons_row.addWidget(self.dict_next)

        self.browse = QPushButton(parent=self.dict_group)
        self.browse.setObjectName("browse")
        dict_buttons_row.addWidget(self.browse)

        dict_layout.addLayout(dict_buttons_row)

        dict_content_row = QHBoxLayout()

        self.tabWidget = QTabWidget(parent=self.dict_group)
        self.tabWidget.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.tabWidget.setObjectName("tabWidget")

        self.tab_1 = QWidget()
        self.tab_1.setObjectName("tab_1")
        tab1_layout = QVBoxLayout(self.tab_1)
        tab1_layout.setContentsMargins(0, 0, 0, 0)
        self.definition_preview = DefinitionWebView(parent=self.tab_1)
        self.definition_preview.setAutoFillBackground(True)
        self.definition_preview.setObjectName("definition_preview")
        tab1_layout.addWidget(self.definition_preview)
        self.tabWidget.addTab(self.tab_1, "")

        self.tab_2 = QWidget()
        self.tab_2.setObjectName("tab_2")
        tab2_layout = QVBoxLayout(self.tab_2)
        tab2_layout.setContentsMargins(0, 0, 0, 0)
        self.definition_source = QTextEdit(parent=self.tab_2)
        self.definition_source.setReadOnly(True)
        self.definition_source.setObjectName("definition_source")
        tab2_layout.addWidget(self.definition_source)
        self.tabWidget.addTab(self.tab_2, "")

        dict_content_row.addWidget(self.tabWidget, 1)

        right_column = QVBoxLayout()

        self.word = QLineEdit(parent=self.dict_group)
        self.word.setObjectName("word")
        self.word.setMaxLength(30)
        self.word.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_column.addWidget(self.word)

        self.search = QPushButton(parent=self.dict_group)
        self.search.setObjectName("search")
        right_column.addWidget(self.search)

        right_column.addStretch()

        self.label_7 = QLabel(parent=self.dict_group)
        self.label_7.setObjectName("label_7")
        self.label_7.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_column.addWidget(self.label_7)

        self.text_format = QComboBox(parent=self.dict_group)
        self.text_format.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.text_format.setObjectName("text_format")
        right_column.addWidget(self.text_format)

        dict_content_row.addLayout(right_column)

        dict_layout.addLayout(dict_content_row)

        main_layout.addWidget(self.dict_group)

        self.note_group = QGroupBox(parent=Dialog)
        self.note_group.setObjectName("note_group")
        note_layout = QGridLayout(self.note_group)

        self.label_2 = QLabel(parent=self.note_group)
        self.label_2.setObjectName("label_2")
        note_layout.addWidget(self.label_2, 0, 0)
        self.note_type = QComboBox(parent=self.note_group)
        self.note_type.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.note_type.setObjectName("note_type")
        note_layout.addWidget(self.note_type, 0, 1)

        self.label_3 = QLabel(parent=self.note_group)
        self.label_3.setObjectName("label_3")
        note_layout.addWidget(self.label_3, 1, 0)
        self.source_field = QComboBox(parent=self.note_group)
        self.source_field.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.source_field.setObjectName("source_field")
        note_layout.addWidget(self.source_field, 1, 1)

        self.label_4 = QLabel(parent=self.note_group)
        self.label_4.setObjectName("label_4")
        note_layout.addWidget(self.label_4, 2, 0)
        self.destination_field = QComboBox(parent=self.note_group)
        self.destination_field.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.destination_field.setObjectName("destination_field")
        note_layout.addWidget(self.destination_field, 2, 1)

        overwrite_row = QHBoxLayout()
        self.label_5 = QLabel(parent=self.note_group)
        self.label_5.setObjectName("label_5")
        overwrite_row.addWidget(self.label_5)
        self.overwrite_destination = QCheckBox(parent=self.note_group)
        self.overwrite_destination.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.overwrite_destination.setText("")
        self.overwrite_destination.setObjectName("overwrite_destination")
        overwrite_row.addWidget(self.overwrite_destination)
        overwrite_row.addStretch()
        note_layout.addLayout(overwrite_row, 3, 0, 1, 2)

        main_layout.addWidget(self.note_group)

        self.start = QPushButton(parent=Dialog)
        self.start.setObjectName("start")
        main_layout.addWidget(self.start)

        self.definition_preview.settings().setAttribute(
            QWebEngineSettings.WebAttribute.JavascriptEnabled, False
        )
        self.retranslateUi(Dialog)
        self.tabWidget.setCurrentIndex(0)
        QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Waydict"))
        self.start.setText(_translate("Dialog", "Add definition"))
        self.label_3.setText(_translate("Dialog", "Source field"))
        self.label_4.setText(_translate("Dialog", "Destination field"))
        self.label_2.setText(_translate("Dialog", "Note type"))
        self.label_5.setText(_translate("Dialog", "Overwrite destination"))
        self.search.setText(_translate("Dialog", "Search"))
        self.tabWidget.setTabText(
            self.tabWidget.indexOf(self.tab_1), _translate("Dialog", "Preview")
        )
        self.definition_source.setPlaceholderText(
            _translate(
                "Dialog",
                'The definition of the word should appear here after pressing the "search" button.',
            )
        )
        self.tabWidget.setTabText(
            self.tabWidget.indexOf(self.tab_2), _translate("Dialog", "Source")
        )
        self.browse.setText(_translate("Dialog", "Browse"))
        self.label_7.setText(_translate("Dialog", "Text format"))
        self.dict_group.setTitle(_translate("Dialog", "Dictionary options"))
        self.note_group.setTitle(_translate("Dialog", "Note options"))
        self.word.setPlaceholderText(_translate("Dialog", "Enter a word"))
        self.dictionary.setPlaceholderText(
            _translate("Dialog", "Select your dictionary")
        )
