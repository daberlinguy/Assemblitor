"""Options-Dialog fuer Themes, Farben und Assembler-Grenzen."""

from PyQt6 import QtWidgets, QtGui

from program.source import PackHandler as pck


class OptionsDialog(QtWidgets.QDialog):
    """Dialog zum Anpassen von Sprache, Theme, Farben und Limits."""
    def __init__(self, parent: QtWidgets.QWidget, ph: pck.ProfileHandler, lh: pck.LangHandler, color_keys: list[str]):
        # Baut Scroll-Layout mit Appearance-, Farb- und Assembler-Abschnitten.
        super().__init__(parent)
        self.ph = ph
        self.lh = lh
        self.color_keys = color_keys
        self.setWindowTitle(lh.opt_win("title"))
        self.resize(520, 640)

        outer = QtWidgets.QVBoxLayout(self)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        content = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(content)

        appearance_box = QtWidgets.QGroupBox(lh.opt_win("Appearance"))
        a_layout = QtWidgets.QFormLayout(appearance_box)
        self.theme_combo = QtWidgets.QComboBox()
        self.theme_combo.addItems(["light", "dark"])
        self.theme_combo.setCurrentText(ph.theme())
        self.lang_combo = QtWidgets.QComboBox()
        langs = lh.gt_langs_with_names()
        self.lang_combo.addItems(langs.values())
        self.lang_key_by_name = {v: k for k, v in langs.items()}
        self.lang_combo.setCurrentText(lh.gt_lang_name(ph.language()))
        self.font_combo = QtWidgets.QFontComboBox()
        self.font_combo.setCurrentText(ph.code_font_face())
        self.font_size = QtWidgets.QSpinBox()
        self.font_size.setRange(5, 48)
        self.font_size.setValue(ph.code_font_size())
        a_layout.addRow(lh.opt_win("LightTheme"), self.theme_combo)
        a_layout.addRow(lh.opt_win("Language"), self.lang_combo)
        a_layout.addRow(lh.opt_win("EditorFont"), self.font_combo)
        a_layout.addRow(lh.opt_win("EditorFont") + " size", self.font_size)

        color_box = QtWidgets.QGroupBox(lh.opt_win("Colors"))
        color_layout = QtWidgets.QFormLayout(color_box)
        self.color_edits = {}
        self._load_colors_for_theme()
        for key in self.color_keys:
            row = QtWidgets.QHBoxLayout()
            edit = QtWidgets.QLineEdit(self)
            edit.setText(self.theme_colors.get(key, ""))
            btn = QtWidgets.QPushButton(lh.opt_win("PickColor"))
            btn.clicked.connect(lambda _, k=key, e=edit: self._pick_color(k, e))
            row.addWidget(edit)
            row.addWidget(btn)
            container = QtWidgets.QWidget()
            container.setLayout(row)
            color_layout.addRow(lh.opt_win("ColorLabels").get(key, key), container)
            self.color_edits[key] = edit

        layout.addWidget(appearance_box)
        layout.addWidget(color_box)

        asm_box = QtWidgets.QGroupBox(lh.opt_win("Assembler"))
        asm_layout = QtWidgets.QFormLayout(asm_box)
        self.min_adr_len = QtWidgets.QSpinBox()
        self.min_adr_len.setRange(1, 10)
        self.min_adr_len.setValue(ph.min_adr_len())
        self.max_cels = QtWidgets.QSpinBox()
        self.max_cels.setRange(1, 1048576)
        self.max_cels.setValue(ph.max_cels())
        self.max_jmps = QtWidgets.QSpinBox()
        self.max_jmps.setRange(1, 1048576)
        self.max_jmps.setValue(ph.max_jmps())
        asm_layout.addRow(lh.opt_win("MinAdrLen"), self.min_adr_len)
        asm_layout.addRow(lh.opt_win("MaxCels"), self.max_cels)
        asm_layout.addRow(lh.opt_win("MaxJmps"), self.max_jmps)
        layout.addWidget(asm_box)

        file_box = QtWidgets.QGroupBox(lh.opt_win("File"))
        file_layout = QtWidgets.QFormLayout(file_box)
        self.closing_unsaved = QtWidgets.QComboBox()
        closing_opts = lh.opt_win("ClosingUnsavedOptions")
        for key, display in closing_opts.items():
            self.closing_unsaved.addItem(display, key)
        idx = list(closing_opts.keys()).index(ph.closing_unsaved())
        self.closing_unsaved.setCurrentIndex(idx)
        file_layout.addRow(lh.opt_win("ClosingUnsaved"), self.closing_unsaved)
        layout.addWidget(file_box)

        adv_box = QtWidgets.QGroupBox(lh.opt_win("Advanced"))
        adv_layout = QtWidgets.QVBoxLayout(adv_box)
        self.dev_mode_chk = QtWidgets.QCheckBox(lh.opt_win("DevMode"))
        self.dev_mode_chk.setChecked(ph.dev_mode())
        adv_layout.addWidget(self.dev_mode_chk)
        layout.addWidget(adv_box)

        scroll.setWidget(content)
        outer.addWidget(scroll)

        btn_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        outer.addWidget(btn_box)

    def accept(self) -> None:  # noqa: D401 (Qt override)
        """Speichert alle Einstellungen zurueck ins Profil."""
        self.ph.save_profile_data("theme", self.theme_combo.currentText())
        lang_display = self.lang_combo.currentText()
        lang_id = self.lang_key_by_name.get(lang_display, self.ph.language())
        self.ph.save_profile_data("language", lang_id)
        self.ph.save_profile_data("code_font_face", self.font_combo.currentText())
        self.ph.save_profile_data("code_font_size", self.font_size.value())
        self.ph.save_profile_data("min_adr_len", self.min_adr_len.value())
        self.ph.save_profile_data("max_cels", self.max_cels.value())
        self.ph.save_profile_data("max_jmps", self.max_jmps.value())
        self.ph.save_profile_data("closing_unsaved", self.closing_unsaved.currentData())
        self.ph.save_profile_data("dev_mode", self.dev_mode_chk.isChecked())
        palette = {}
        for key, edit in self.color_edits.items():
            palette[key] = edit.text().strip()
        self.ph.save_theme_colors(self.theme_combo.currentText(), palette)
        super().accept()

    def _pick_color(self, key: str, edit: QtWidgets.QLineEdit):
        """Oeffnet Farb-Dialog und schreibt Hexwert ins Feld."""
        col = QtWidgets.QColorDialog.getColor(QtGui.QColor(edit.text()), self, "Pick color")
        if col.isValid():
            edit.setText(col.name())

    def _load_colors_for_theme(self):
        """Liest Farbpalette fuer aktuelles Theme aus Profil."""
        self.theme_colors = self.ph.colors(self.theme_combo.currentText())
