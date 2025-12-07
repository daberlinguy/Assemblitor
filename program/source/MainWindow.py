"""Qt-Hauptfenster fuer Assemblitor.

Dieses Modul baut die komplette Qt-Oberflaeche: Menues, Toolbar,
Statusanzeige sowie die Ein- und Ausgabe-Editoren. Die Logik fuer
Emulator, Pack- und Profil-Handling kommt aus program.source.*.
"""

import sys
from pathlib import Path
from typing import Optional

from PyQt6 import QtWidgets, QtGui, QtCore

from program.source import Emulator as emu
from program.source import PackHandler as pck
from program.source.Editors import InputEditor, OutputViewer
from program.source.Options import OptionsDialog

# Sprites liegen unter program/sprites (eine Ebene ueber source).
SPRITE_DIR = Path(__file__).resolve().parent.parent / "sprites"


class QtEditorWindow(QtWidgets.QMainWindow):
    """Hauptfenster: kapselt UI, Menues, Toolbar und Status-Widgets."""
    def __init__(self, profile_dir: Path, root_dir: Path, dev_mode: bool = False):
        # Lade Profile, Sprache, Fehler-Handler und Emulator.
        super().__init__()
        self.ph = pck.ProfileHandler(profile_dir)
        self.lh = pck.LangHandler(self.ph.language())
        self.eh = pck.ErrorHandler()
        self.emu = emu.Emulator()
        emu.startup(profile_handler=self.ph, error_handler=self.eh)

        if dev_mode:
            self.ph.save_profile_data("dev_mode", dev_mode)
        self.dev_mode = self.ph.dev_mode()
        self.root_dir = root_dir
        self.fonts_dir = root_dir / "fonts"
        self._register_bundled_fonts()
        self.file_path: Optional[str] = None
        self.last_dir = root_dir
        self.dirty_flag = False
        self.active_theme = self.ph.theme()
        self.active_language = self.ph.language()
        self.palette = self.ph.colors(self.active_theme)

        preferred_face = self.ph.code_font_face()
        if hasattr(self, "bundled_font_family") and preferred_face == "JetBrains Mono":
            preferred_face = self.bundled_font_family
        self.code_font = QtGui.QFont(preferred_face, self.ph.code_font_size())
        self.icon_theme = self.active_theme
        self.color_keys = [
            "base_bg",
            "base_fg",
            "text_bg",
            "text_fg",
            "cursor_color",
            "error_color",
            "accent_color",
            "highlight_base_bg",
            "highlight_text_bg",
            "highlight_text_fg",
            "comment_color",
        ]

        self._build_ui()
        self._connect_signals()
        self._update_title(self.lh.gui("title"))
        self._apply_app_icon()

    def _build_ui(self):
        """Rahmenaufbau: Fenster, Actions, Menues, Toolbar, Center."""
        self.resize(960, 640)
        self.setMinimumSize(640, 480)
        self._build_actions()
        self._build_menus()
        self._build_toolbar()
        self._build_central()

    def _build_actions(self):
        """Alle Actions mit Texten, Shortcuts und Icons erstellen."""
        lg = self.lh.gui
        self.act_new = QtGui.QAction(lg("New"), self)
        self.act_open = QtGui.QAction(lg("Open"), self)
        self.act_reload = QtGui.QAction(lg("Reload"), self)
        self.act_save = QtGui.QAction(lg("Save"), self)
        self.act_save_as = QtGui.QAction(lg("SaveAs"), self)
        self.act_exit = QtGui.QAction(lg("Exit"), self)
        self.act_options = QtGui.QAction(lg("Options"), self)
        self.act_run = QtGui.QAction(lg("RunPrg"), self)
        self.act_step = QtGui.QAction(lg("RunStep"), self)
        self.act_demo = QtGui.QAction(lg("DemoPrg"), self)
        self.act_lang_help = QtGui.QAction(lg("ShowLangPack"), self)
        self.act_options.triggered.connect(self.open_options)
        self.act_lang_help.triggered.connect(self.show_language_pack)

        self.act_new.setShortcut(QtGui.QKeySequence("Ctrl+N"))
        self.act_open.setShortcut(QtGui.QKeySequence("Ctrl+O"))
        self.act_reload.setShortcut(QtGui.QKeySequence("Ctrl+R"))
        self.act_save.setShortcut(QtGui.QKeySequence("Ctrl+S"))
        self.act_save_as.setShortcut(QtGui.QKeySequence("Ctrl+Shift+S"))
        self.act_run.setShortcut(QtGui.QKeySequence("F5"))
        self.act_step.setShortcut(QtGui.QKeySequence("Shift+F5"))

        self.act_run.setIcon(self._load_icon("run_BTN", "default"))
        self.act_step.setIcon(self._load_icon("step_BTN", "default"))

    def _build_menus(self):
        """Menueleiste samt File-/Help-Menues aufbauen."""
        lg = self.lh.gui
        menubar = self.menuBar()
        file_menu = menubar.addMenu(lg("File"))
        file_menu.addAction(self.act_new)
        file_menu.addAction(self.act_open)
        file_menu.addAction(self.act_reload)
        file_menu.addAction(self.act_save)
        file_menu.addAction(self.act_save_as)
        file_menu.addSeparator()
        file_menu.addAction(self.act_options)
        file_menu.addSeparator()
        file_menu.addAction(self.act_exit)

        help_menu = menubar.addMenu(lg("Help"))
        help_menu.addAction(self.act_lang_help)
        help_menu.addAction(self.act_demo)

    def _build_toolbar(self):
        """Toolbar mit Run/Step, Abstandhalter und Statusfeldern."""
        toolbar = QtWidgets.QToolBar("Main Toolbar", self)
        toolbar.setMovable(False)
        self.addToolBar(QtCore.Qt.ToolBarArea.TopToolBarArea, toolbar)
        toolbar.addAction(self.act_run)
        toolbar.addAction(self.act_step)

        toolbar.addSeparator()
        spacer = QtWidgets.QWidget()
        spacer.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Preferred)
        toolbar.addWidget(spacer)

        status_frame = QtWidgets.QFrame()
        status_frame.setFrameShape(QtWidgets.QFrame.Shape.Box)
        status_frame.setFrameShadow(QtWidgets.QFrame.Shadow.Plain)
        status_layout = QtWidgets.QHBoxLayout(status_frame)
        status_layout.setContentsMargins(12, 8, 12, 8)
        status_layout.setSpacing(16)

        def make_stat_block(title: str):
            # Kleiner VBox-Block mit Ueberschrift und Wertlabel.
            box = QtWidgets.QWidget()
            v = QtWidgets.QVBoxLayout(box)
            v.setContentsMargins(0, 0, 0, 0)
            v.setSpacing(4)
            lbl_title = QtWidgets.QLabel(title)
            lbl_title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            lbl_val = QtWidgets.QLabel("0")
            lbl_val.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            lbl_val.setMinimumWidth(48)
            lbl_val.setFrameShape(QtWidgets.QFrame.Shape.Box)
            lbl_val.setLineWidth(1)
            v.addWidget(lbl_title)
            v.addWidget(lbl_val)
            return box, lbl_val

        pc_box, self.lbl_pc_val = make_stat_block("PC")
        akku_box, self.lbl_accu_val = make_stat_block("ACC")

        ir_box = QtWidgets.QWidget()
        ir_layout = QtWidgets.QVBoxLayout(ir_box)
        ir_layout.setContentsMargins(0, 0, 0, 0)
        ir_layout.setSpacing(4)
        ir_label = QtWidgets.QLabel("IR")
        ir_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        ir_values = QtWidgets.QHBoxLayout()
        ir_values.setContentsMargins(0, 0, 0, 0)
        ir_values.setSpacing(6)
        self.lbl_ir_left = QtWidgets.QLabel("-")
        self.lbl_ir_right = QtWidgets.QLabel("-")
        for lbl in (self.lbl_ir_left, self.lbl_ir_right):
            lbl.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            lbl.setMinimumWidth(38)
            lbl.setFrameShape(QtWidgets.QFrame.Shape.Box)
            lbl.setLineWidth(1)
        ir_values.addWidget(self.lbl_ir_left)
        ir_values.addWidget(self.lbl_ir_right)
        ir_layout.addWidget(ir_label)
        ir_layout.addLayout(ir_values)

        status_layout.addWidget(pc_box)
        status_layout.addWidget(akku_box)
        status_layout.addWidget(ir_box)
        status_frame.setStyleSheet("")
        toolbar.addWidget(status_frame)
        self._status_frame = status_frame
        self._apply_status_colors()

    def _build_central(self):
        """Splitter mit Eingabe- und Ausgabe-Editor anlegen."""
        splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        self.inp_editor = InputEditor(splitter, self.palette, self.code_font)
        self.out_viewer = OutputViewer(splitter, self.palette, self.code_font)
        self.out_viewer.setReadOnly(True)
        splitter.addWidget(self.inp_editor)
        splitter.addWidget(self.out_viewer)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 2)
        self.setCentralWidget(splitter)
        self.setStyleSheet(
            """
            QMainWindow { background: %(bg)s; color: %(fg)s; }
            QMenuBar, QMenu { background: %(bg)s; color: %(fg)s; }
            """
            % {"bg": self.palette.get("base_bg", "#222"), "fg": self.palette.get("base_fg", "#444")}
        )

    def _connect_signals(self):
        """Signalverkabelung fuer Buttons, Menues und Editor."""
        self.act_new.triggered.connect(lambda *_: self.open_prg())
        self.act_open.triggered.connect(self.open_file)
        self.act_reload.triggered.connect(self.reload_file)
        self.act_save.triggered.connect(self.save_file)
        self.act_save_as.triggered.connect(self.save_file_as)
        self.act_exit.triggered.connect(self.close)
        self.act_run.triggered.connect(lambda: self.run(execute_all=True))
        self.act_step.triggered.connect(lambda: self.run(execute_all=False))
        self.act_demo.triggered.connect(self.open_demo_prg)
        self.inp_editor.textChanged.connect(self._on_dirty)

    def _on_dirty(self):
        """Setzt Dirty-Flag, wenn Text sich aendert."""
        text = self.inp_editor.toPlainText()
        if hasattr(self, "init_inp") and text == getattr(self, "init_inp", ""):
            self._set_dirty(False)
        else:
            self._set_dirty(True)

    def _set_dirty(self, new_state: bool):
        """Aktualisiert Dirty-Status und Fenstertitel."""
        if getattr(self, "dirty_flag", False) != new_state:
            self.dirty_flag = new_state
            title = self.windowTitle().lstrip("*")
            self._update_title(title, dirty=new_state)

    def _update_title(self, base: str, dirty: bool = False):
        """Prefix * bei ungespeicherten Aenderungen."""
        if dirty:
            self.setWindowTitle(f"*{base}")
        else:
            self.setWindowTitle(base)

    def run(self, execute_all: bool):
        """Fuehrt Programm komplett oder schrittweise aus und aktualisiert Status."""
        inp = self.inp_editor.toPlainText()
        try:
            prg_output, pc, accu, ireg = self.emu.gt_out(inp, execute_all)
            self.out_viewer.display_output(
                prg_output[0],
                prg_output[1],
                prg_output[2],
                self.palette.get("error_color", "#f00"),
            )
            self.lbl_pc_val.setText(str(pc))
            self.lbl_accu_val.setText(str(accu))
            self.lbl_ir_left.setText(str(ireg[0]))
            self.lbl_ir_right.setText(str(ireg[1]))
        except Exception as exc:  # pragma: no cover - placeholder error view
            stack = ""  # stacktrace can be wired later
            self.out_viewer.display_error(
                str(exc),
                stacktrace="",
                prg_state=str(self.emu.prg) if self.emu.prg else None,
                expand_trace=self.dev_mode,
            )

    def open_file(self):
        """Oeffnet Datei per Dialog und laedt den Inhalt."""
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            self.lh.file_mng("OpenFile"),
            str(self.last_dir),
            "Asm Files (*.asm);;Text Files (*.txt);",
        )
        if path:
            self.file_path = path
            self.last_dir = Path(path).parent
            with open(path, "r", encoding="utf-8") as f:
                data = f.read()
            self.open_prg(data, win_title=f"{path} - {self.lh.gui('title')}")

    def reload_file(self):
        """Laedt aktuelle Datei neu von Disk."""
        if self.file_path:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = f.read()
            self.open_prg(data, win_title=f"{self.file_path} - {self.lh.gui('title')}")

    def save_file(self):
        """Speichert aktuelle Datei an bestehendem Pfad."""
        if self.file_path:
            text = self.inp_editor.toPlainText()
            with open(self.file_path, "w", encoding="utf-8") as f:
                f.write(text)
            self.init_inp = text
            self._set_dirty(False)

    def save_file_as(self):
        """Speichert Datei unter neuem Pfad."""
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            self.lh.file_mng("SaveFile"),
            str(self.last_dir),
            "Asm Files (*.asm);;Text Files (*.txt);",
        )
        if path:
            self.file_path = path
            self.last_dir = Path(path).parent
            self.save_file()
            self._update_title(f"{path} - {self.lh.gui('title')}")

    def open_prg(self, prg_str: str = "", win_title: Optional[str] = None):
        """Setzt Editorinhalt, Titel und Dirty-Flag zurueck."""
        self.inp_editor.blockSignals(True)
        self.inp_editor.setPlainText(prg_str)
        self.inp_editor.blockSignals(False)
        self.init_inp = prg_str
        self._set_dirty(False)
        if win_title:
            self._update_title(win_title)
        else:
            self._update_title(self.lh.gui("title"))

    def open_demo_prg(self):
        """Laedt Demo-Programm aus Sprachpaket."""
        self.open_prg(self.lh.demo())

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:  # noqa: N802 (Qt API)
        """Fragt bei ungespeicherten Aenderungen nach Bestaetigung."""
        if self.dirty_flag and not self.dev_mode:
            res = QtWidgets.QMessageBox.question(
                self,
                self.lh.file_mng("UnsavedChanges"),
                self.lh.file_mng("Save?"),
                QtWidgets.QMessageBox.StandardButton.Yes
                | QtWidgets.QMessageBox.StandardButton.No
                | QtWidgets.QMessageBox.StandardButton.Cancel,
            )
            if res == QtWidgets.QMessageBox.StandardButton.Yes:
                self.save_file()
                if self.dirty_flag:
                    event.ignore()
                    return
            elif res == QtWidgets.QMessageBox.StandardButton.Cancel:
                event.ignore()
                return
        event.accept()

    def _load_icon(self, group: str, state: str) -> QtGui.QIcon:
        """Laedt Toolbar-Icons aus Sprites nach Theme/Status."""
        fname = f"{state}_{self.icon_theme}.png"
        path = SPRITE_DIR / group / fname
        if path.exists():
            return QtGui.QIcon(str(path))
        return QtGui.QIcon()

    def _apply_app_icon(self):
        """Setzt Anwendungs-Icon fuer Fenster/Dock."""
        app_icon_path = SPRITE_DIR / "Assemblitor" / "icon.png"
        if app_icon_path.exists():
            icon = QtGui.QIcon(str(app_icon_path))
            self.setWindowIcon(icon)
            QtWidgets.QApplication.instance().setWindowIcon(icon)

    def _register_bundled_fonts(self):
        """Registriert gebuendelte JetBrains-Mono-Schriften."""
        # Load bundled JetBrains Mono fonts so the default face is available even without a system install.
        if not self.fonts_dir.exists():
            return
        loaded_ids = []
        patterns = ["JetBrainsMono*.ttf", "JetBrainsMono*.otf"]
        for pattern in patterns:
            for font_path in self.fonts_dir.glob(pattern):
                font_id = QtGui.QFontDatabase.addApplicationFont(str(font_path))
                if font_id != -1:
                    loaded_ids.append(font_id)
        if loaded_ids:
            families = []
            for fid in loaded_ids:
                families.extend(QtGui.QFontDatabase.applicationFontFamilies(fid))
            if families:
                # Use the first family as the preferred bundled name.
                self.bundled_font_family = families[0]
            else:
                self.bundled_font_family = "JetBrains Mono"

    def show_language_pack(self):
        """Zeigt den aktuellen Sprach-Pack-Inhalt in einem Dialog."""
        lang_id = self.active_language
        lang_path = Path(pck.program_dir) / "languages" / f"{lang_id}.dict"
        if not lang_path.exists():
            QtWidgets.QMessageBox.warning(self, self.lh.gui("Help"), f"Language file not found: {lang_path}")
            return
        try:
            data = pck.ph.gt_pack_data(lang_id, f"{pck.program_dir}/languages")
        except Exception:
            with open(lang_path, "r", encoding="utf-8") as f:
                raw = f.read()
            formatted = raw
        else:
            formatted = self._pretty_lang_dump(data)

        dlg = QtWidgets.QDialog(self)
        dlg.setWindowTitle(f"{self.lh.gui('Help')} - {self.lh.gt_lang_name(lang_id)}")
        layout = QtWidgets.QVBoxLayout(dlg)
        text = QtWidgets.QPlainTextEdit()
        text.setReadOnly(True)
        text.setPlainText(formatted)
        text.setFont(QtGui.QFont(self.code_font.family(), max(10, self.code_font.pointSize())))
        layout.addWidget(text)
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(dlg.reject)
        buttons.accepted.connect(dlg.accept)
        layout.addWidget(buttons)
        dlg.resize(720, 560)
        dlg.exec()

    def _pretty_lang_dump(self, data: dict) -> str:
        """Formatiert Sprachdaten in lesbares Textlayout."""
        lines = []

        def emit_section(title: str):
            lines.append(title)
            lines.append("-" * len(title))

        def emit_mapping(mapping: dict, indent: int = 0):
            pad = " " * indent
            for k, v in mapping.items():
                if isinstance(v, dict):
                    lines.append(f"{pad}{k}:")
                    emit_mapping(v, indent + 2)
                elif isinstance(v, (list, tuple)):
                    lines.append(f"{pad}{k}:")
                    for item in v:
                        lines.append(f"{pad}  - {item}")
                else:
                    lines.append(f"{pad}{k}: {v}")

        # Info
        if "info" in data:
            emit_section("Info")
            emit_mapping(data["info"], 2)
            lines.append("")

        for sec in ("file_mng", "gui", "opt_win", "asm_win"):
            if sec in data:
                emit_section(sec)
                emit_mapping(data[sec], 2)
                lines.append("")

        if "demo" in data:
            emit_section("demo")
            lines.append(data["demo"])

        return "\n".join(lines)

    def open_options(self):
        """Oeffnet Optionsdialog und uebernimmt neue Einstellungen."""
        dlg = OptionsDialog(self, self.ph, self.lh, self.color_keys)
        if dlg.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            preferred_face = self.ph.code_font_face()
            if hasattr(self, "bundled_font_family") and preferred_face == "JetBrains Mono":
                preferred_face = self.bundled_font_family
            self.code_font = QtGui.QFont(preferred_face, self.ph.code_font_size())
            self.palette = self.ph.colors(self.ph.theme())
            self.inp_editor.setFont(self.code_font)
            self.out_viewer.setFont(self.code_font)
            self.inp_editor.palette = self.palette
            self.out_viewer.palette = self.palette
            self.inp_editor.highlighter.set_palette(self.palette)
            self.out_viewer.highlighter.set_palette(self.palette)
            self._update_title(self.lh.gui("title"))
            self.active_theme = self.ph.theme()
            self.active_language = self.ph.language()
            self.dev_mode = self.ph.dev_mode()
            self.inp_editor.setStyleSheet(self.inp_editor._style_from_palette())
            self.out_viewer.setStyleSheet(self.out_viewer._style_from_palette())
            self._apply_status_colors()
            self.setStyleSheet(
                """
                QMainWindow { background: %(bg)s; color: %(fg)s; }
                QMenuBar, QMenu { background: %(bg)s; color: %(fg)s; }
                """
                % {"bg": self.palette.get("base_bg", "#222"), "fg": self.palette.get("base_fg", "#444")}
            )

    def _apply_status_colors(self):
        """Wendet Palettenfarben auf Status-Widgets an."""
        # Use theme colors: background same as app, borders from the configurable accent.
        fg = self.palette.get("base_fg", "#444444")
        border = self.palette.get("accent_color", "#ff9f1c")
        outer_bg = self.palette.get("base_bg", "#222222")
        inner_border = border
        box_bg = self.palette.get("base_bg", "#222222")
        for lbl in (
            self.lbl_pc_val,
            self.lbl_accu_val,
            self.lbl_ir_left,
            self.lbl_ir_right,
        ):
            lbl.setStyleSheet(
                """
                QLabel { color: %(fg)s; background: %(bg)s; border: 1px solid %(border)s; border-radius: 2px; }
                """
                % {"fg": fg, "bg": box_bg, "border": inner_border}
            )
        if hasattr(self, "_status_frame"):
            self._status_frame.setStyleSheet(
                """
                QFrame { border: 2px solid %(border)s; background: %(bg)s; border-radius: 4px; }
                QLabel { color: %(fg)s; }
                """
                % {"border": border, "bg": outer_bg, "fg": fg}
            )


def main(profile_dir: Path, root_dir: Path, dev_mode: bool = False):
    app = QtWidgets.QApplication(sys.argv)
    # Ensure dock/taskbar icon is set before any windows show.
    app_icon_path = SPRITE_DIR / "Assemblitor" / "icon.png"
    if app_icon_path.exists():
        app.setWindowIcon(QtGui.QIcon(str(app_icon_path)))
    win = QtEditorWindow(profile_dir=profile_dir, root_dir=root_dir, dev_mode=dev_mode)
    win.show()
    app.exec()
