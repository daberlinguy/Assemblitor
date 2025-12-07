"""Editor-Widgets fuer Eingabe und Ausgabe.

Enthaelt Syntax-Highlighting fuer Kommentare, Adress-Autoinkrement im
Eingabefeld sowie Fehlermeldungsdarstellung im Ausgabefeld.
"""

from typing import Optional

from PyQt6 import QtWidgets, QtGui, QtCore


class CommentHighlighter(QtGui.QSyntaxHighlighter):
    """Highlights comments starting at ';' using the provided palette."""

    def __init__(self, doc: QtGui.QTextDocument, palette: dict):
        super().__init__(doc)
        self.comment_format = QtGui.QTextCharFormat()
        self.set_palette(palette)

    def set_palette(self, palette: dict):
        self.palette = palette
        self.comment_format.setForeground(QtGui.QColor(palette.get("comment_color", "#777777")))
        self.rehighlight()

    def highlightBlock(self, text: str) -> None:  # noqa: N802 (Qt API)
        if ";" in text:
            idx = text.find(";")
            self.setFormat(idx, len(text) - idx, self.comment_format)


class InputEditor(QtWidgets.QPlainTextEdit):
    """Input editor with address auto-increment on Enter and shift+Enter passthrough."""

    def __init__(self, parent, palette: dict, code_font: QtGui.QFont):
        # Setzt Fonts, Palettenfarben und Kommentar-Highlighter.
        super().__init__(parent)
        self.palette = palette
        self.setFont(code_font)
        self.setWordWrapMode(QtGui.QTextOption.WrapMode.NoWrap)
        self.setLineWrapMode(QtWidgets.QPlainTextEdit.LineWrapMode.NoWrap)
        self.setPlaceholderText("Enter assembly code...")
        self.setTabChangesFocus(False)
        self.setStyleSheet(self._style_from_palette())
        self.highlighter = CommentHighlighter(self.document(), self.palette)

    def _style_from_palette(self) -> str:
        return (
            f"QPlainTextEdit {{ background: {self.palette.get('text_bg', '#333')};"
            f" color: {self.palette.get('text_fg', '#fff')};"
            f" selection-background-color: {self.palette.get('highlight_text_bg', '#555')};"
            f" selection-color: {self.palette.get('highlight_text_fg', '#000')}; }}"
        )

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:  # noqa: N802 (Qt API)
        # Enter -> naechste Adresse einfuegen, Shift+Enter -> normale Zeile.
        if event.key() in (QtCore.Qt.Key.Key_Return, QtCore.Qt.Key.Key_Enter):
            if event.modifiers() & QtCore.Qt.KeyboardModifier.ShiftModifier:
                super().keyPressEvent(event)  # plain newline
            else:
                self.insert_next_address_line()
            return
        super().keyPressEvent(event)

    def insert_next_address_line(self):
        """Fuegt neue Zeile mit auto-inkrementierter Adresse ein."""
        cursor = self.textCursor()
        cursor.beginEditBlock()
        cursor.select(QtGui.QTextCursor.SelectionType.LineUnderCursor)
        line_text = cursor.selectedText()
        next_adr = self._compute_next_address(line_text)
        cursor.movePosition(QtGui.QTextCursor.MoveOperation.EndOfLine)
        cursor.insertText("\n")
        if next_adr is not None:
            cursor.insertText(next_adr)
        cursor.endEditBlock()
        self.setTextCursor(cursor)

    def _compute_next_address(self, line: str) -> Optional[str]:
        """Berechnet naechste Adresse anhand aktueller Zeile."""
        cell = line.split(";", 1)[0]
        if not cell.strip():
            return None
        parts = cell.lstrip().split()
        if not parts:
            return None
        try:
            adr = int(parts[0])
        except ValueError:
            return None
        next_adr = adr + 1
        width = max(len(parts[0].strip()), 2)
        return f"{next_adr:0{width}d} "


class OutputViewer(QtWidgets.QPlainTextEdit):
    """Read-only output with optional stacktrace toggling."""

    def __init__(self, parent, palette: dict, code_font: QtGui.QFont):
        # Ausgabe-Editor mit Fehlerdarstellung (einklappbar).
        super().__init__(parent)
        self.palette = palette
        self.setReadOnly(True)
        self.setFont(code_font)
        self.setWordWrapMode(QtGui.QTextOption.WrapMode.NoWrap)
        self.setStyleSheet(self._style_from_palette())
        self.error_expanded = False
        self.error_details = {"stacktrace": "", "prg_state": None}
        self.error_user_message = ""
        self.error_header = "Stacktrace"
        self.error_active = False
        self.highlighter = CommentHighlighter(self.document(), self.palette)
        self.setMouseTracking(True)

    def _style_from_palette(self, error_mode: bool = False) -> str:
        """Build stylesheet; keep widget background neutral even in error mode."""
        bg = self.palette.get("text_bg", "#333")
        fg = self.palette.get("text_fg", "#fff")
        # We no longer paint the whole pane red; error coloring happens via text formats.
        return (
            f"QPlainTextEdit {{ background: {bg};"
            f" color: {fg};"
            f" selection-background-color: {self.palette.get('highlight_text_bg', '#555')};"
            f" selection-color: {self.palette.get('highlight_text_fg', '#000')}; }}"
        )

    def clear_all(self):
        """Loescht gesamten Text."""
        self.setPlainText("")

    def display_output(self, code_section1: str, active_code: str, code_section2: str, highlight_color: str):
        """Zeigt normalen Programmausgabe-Text und hebt aktive Zeile hervor."""
        self.error_expanded = False
        self.error_details = {"stacktrace": "", "prg_state": None}
        self.error_user_message = ""
        self.error_active = False
        self.setStyleSheet(self._style_from_palette(error_mode=False))
        merged = code_section1 + active_code + code_section2
        self.setPlainText(merged)
        if active_code:
            cursor = self.textCursor()
            text = self.toPlainText()
            start = text.find(active_code)
            if start != -1:
                cursor.setPosition(start)
                cursor.movePosition(
                    QtGui.QTextCursor.MoveOperation.NextCharacter,
                    QtGui.QTextCursor.MoveMode.KeepAnchor,
                    len(active_code),
                )
                fmt = QtGui.QTextCharFormat()
                fmt.setForeground(QtGui.QColor(self.palette.get("text_fg", "#fff")))
                fmt.setBackground(QtGui.QColor(highlight_color))
                cursor.setCharFormat(fmt)

    def display_error(
        self,
        user_msg: str,
        stacktrace: str = "",
        prg_state: str = None,
        expand_trace: bool = False,
        header_label: str = "Stacktrace",
    ):
        """Zeigt Fehlermeldung; Details koennen aufgeklappt werden."""
        self.error_user_message = user_msg.strip()
        self.error_details = {"stacktrace": stacktrace.strip(), "prg_state": prg_state}
        self.error_expanded = bool(expand_trace and stacktrace)
        self.error_header = header_label
        self.error_active = True
        self.setStyleSheet(self._style_from_palette(error_mode=False))
        self._render_error(header_label)

    def _render_error(self, header_label: str):
        """Rendert Fehlermeldung und markiert nur die Hauptzeile."""
        self.clear_all()
        parts = [self.error_user_message]
        if self.error_details["stacktrace"] or self.error_details["prg_state"]:
            arrow = "▼" if self.error_expanded else "▶"
            parts.append(f"{arrow} {header_label}")
            if self.error_expanded and self.error_details["stacktrace"]:
                parts.append(self.error_details["stacktrace"])
            if self.error_expanded and self.error_details["prg_state"]:
                parts.append(self.error_details["prg_state"])
        self.setPlainText("\n\n".join(parts))
        if self.error_active:
            # Reset default formatting
            default_fmt = QtGui.QTextCharFormat()
            default_fmt.setForeground(QtGui.QColor(self.palette.get("text_fg", "#fff")))
            cursor = self.textCursor()
            cursor.select(QtGui.QTextCursor.SelectionType.Document)
            cursor.setCharFormat(default_fmt)

            # Highlight only the first line (primary error message)
            text = self.toPlainText()
            first_break = text.find("\n")
            first_len = len(text) if first_break == -1 else first_break
            cursor = self.textCursor()
            cursor.setPosition(0)
            cursor.movePosition(
                QtGui.QTextCursor.MoveOperation.NextCharacter,
                QtGui.QTextCursor.MoveMode.KeepAnchor,
                first_len,
            )
            err_fmt = QtGui.QTextCharFormat()
            err_fmt.setBackground(QtGui.QColor(self.palette.get("error_color", "#c00")))
            err_fmt.setForeground(QtGui.QColor(self.palette.get("highlight_text_fg", "#000")))
            cursor.setCharFormat(err_fmt)

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:  # noqa: N802 (Qt API)
        """Toggle error details on click when an error is displayed."""
        if self.error_details["stacktrace"] or self.error_details["prg_state"]:
            self.error_expanded = not self.error_expanded
            self._render_error(self.error_header)
        super().mousePressEvent(event)
