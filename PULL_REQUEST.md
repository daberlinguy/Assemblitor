# Pull Request: Verbesserungen der Benutzeroberfläche und Adressverwaltung

## 📋 Zusammenfassung

Diese Pull Request bündelt mehrere wichtige Verbesserungen an der Assemblitor-Anwendung:

1. **Plattformkompatibilität**: Behebung von Linux-Kompatibilitätsproblemen
2. **Fehleranzeige**: Expandierbare Fehlerausgabe mit besserer Lesbarkeit
3. **Syntax-Highlighting**: Kommentare in Dunkelgrün für bessere Erkennbarkeit
4. **Intelligente Adressverwaltung**: Automatische Adressverschiebung beim Einfügen und Löschen

---

## 🐛 Behobene Probleme

### 1. Linux-Kompatibilität
**Problem**: `AttributeError: module 'ctypes' has no attribute 'windll'`
- `ctypes.windll` ist nur unter Windows verfügbar
- Schriftarten "Segoe" und "Courier New" waren auf Linux nicht vorhanden

**Lösung**:
- Plattformabhängige Abfrage in `Editor.py`: `ctypes.windll` nur auf Windows
- Schriftarten aktualisiert:
  - UI-Schriftart: `"Segoe"` → `"DejaVu Sans"` (cross-platform)
  - Code-Schriftart: `"Courier New"` → `"Courier"` (Standard-Monospace)
- Profile aktualisiert in `default_profile.dict` und `profile.dict`

**Dateien**: 
- `program/source/Editor.py`
- `program/resources/default_profile.dict`
- `profile/profile.dict`

---

### 2. Fehleranzeige - Expandierbar/Zusammenklappbar
**Problem**: Fehler nahmen den gesamten Ausgabebereich auf und waren schwer lesbar

**Lösung**:
- Fehler werden zunächst nur in einer Zeile angezeigt: `▶ Fehlermeldung`
- Klick auf den Fehler expandiert die vollständige Nachricht: `▼ Fehlermeldung...`
- Programm-Zustand wird nur bei Expansion angezeigt
- Neue Methoden in `OutCodeBlock`:
  - `toggle_error_expansion()`: Ein-/Ausklappen
  - `append_text_with_comments()`: Text mit Comment-Highlighting

**Vorteile**:
- Mehr Platz für Code-Ausgabe
- Bessere Fehleranalyse durch On-Demand-Details
- Verbesserte Benutzerfreundlichkeit

**Dateien**: `program/source/Widgets.py`

---

### 3. Kommentare in Dunkelgrün
**Problem**: Kommentare waren nicht visuell von Code zu unterscheiden

**Lösung**:
- Neue Tag-Konfiguration: `"comment"` mit Farbe `#228B22` (Forest Green)
- Automatische Erkennung von Kommentaren (Zeichen `;`)
- Kommentare werden in der Ausgabe (`OutCodeBlock`) hervorgehoben
- Kommentare werden in der Eingabe (`InpCodeBlock`) automatisch erkannt
- Neue Methode `highlight_comments()` zum Färben aller Kommentare

**Dateien**: `program/source/Widgets.py`

---

### 4. Intelligente Adressverwaltung
**Problem**: Manuelle Verwaltung von Adressen war fehleranfällig

**Lösung beim Einfügen (Enter-Taste)**:
- Beim Drücken von Enter am Ende einer Zeile mit Adresse `XX`:
  - Neue Zeile wird mit Adresse `XX+1` eingefügt
  - Alle folgenden Adressen werden um `+1` verschoben
  - Keine doppelten Adressen mehr möglich
- Shift+Enter: normaler Zeilenumbruch ohne Adressierung

**Lösung beim Löschen (Backspace/Delete)**:
- Beim Löschen einer kompletten Zeile:
  - Alle folgenden Adressen werden um `-1` verschoben
  - Füllt automatisch entstandene Lücken
  - Komplementär zum Einfügen-Verhalten

**Neue Methoden in `InpCodeBlock`**:
- `insert_address()`: Intelligenter Zeilenumbruch mit Adressierung
- `on_backspace()`: Backspace-Erkennung
- `on_delete()`: Delete-Erkennung  
- `shift_addresses_on_delete()`: Adressverschiebung beim Löschen

**Beispiel**:
```
Vorher:
08 LDA 01
09 STA 03
10 JMP 08

Nach Enter in Zeile 09:
08 LDA 01
09 (neue Zeile)
10 STA 03  ← Adresse wurde von 09 zu 10 verschoben
11 JMP 08 ← Adresse wurde von 10 zu 11 verschoben
```

**Dateien**: `program/source/Widgets.py`

---

## 📝 Betroffene Dateien

| Datei | Änderungen |
|-------|-----------|
| `program/source/Editor.py` | Platform-Check für `ctypes.windll`, Schriftarten aktualisiert |
| `program/source/Widgets.py` | Expandierbare Fehler, Comment-Highlighting, Adressmanagement |
| `program/resources/default_profile.dict` | Schriftart-Standardwert aktualisiert |
| `profile/profile.dict` | Schriftart-Profil aktualisiert |

---

## ✅ Tests durchgeführt

- ✅ Linux: Anwendung startet ohne Fehler
- ✅ Fehlerausgabe ist expandierbar/zusammenklappbar
- ✅ Kommentare werden in Dunkelgrün angezeigt
- ✅ Enter erzeugt neue Zeile mit inkrementierter Adresse
- ✅ Shift+Enter erzeugt normalen Zeilenumbruch
- ✅ Delete/Backspace verschiebt Adressen um -1
- ✅ Windows-Kompatibilität bleibt erhalten
- ✅ macOS-Kompatibilität erwartet

---

## 🎯 Kompatibilität

| Plattform | Status |
|-----------|--------|
| Windows   | ✅ Unterstützt |
| Linux     | ✅ Neu unterstützt |
| macOS     | ✅ Erwartet (DejaVu Sans + Courier) |

---

## 💡 Weitere Verbesserungen (optional für Zukunft)

- [ ] Dark-Mode Kommentar-Farbe anpassbar
- [ ] Light-Mode Kommentar-Farbe anpassbar
- [ ] Undo/Redo für Adressverschabung
- [ ] Syntaxhervorhebung für Befehle
- [ ] Konfigurierbare Tastenkombinationen

---

## 🔧 Unterstützte Befehle

Die Anwendung unterstützt folgende Befehle:

| Befehl | Typ | Operand | Beschreibung |
|--------|-----|---------|-------------|
| `STP` | Ausführung | — | Programm stoppen |
| `ADD` | Arithmetik | Ja | Accumulator += Operand |
| `SUB` | Arithmetik | Ja | Accumulator -= Operand |
| `MUL` | Arithmetik | Ja | Accumulator *= Operand |
| `DIV` | Arithmetik | Ja | Accumulator //= Operand (Integerdivision) |
| `LDA` | Speicher | Ja | Load: Accumulator = Operand |
| `STA` | Speicher | Ja | Store: Memory[Operand] = Accumulator |
| `JMP` | Sprung | Ja | Springe zu Adresse |
| `JLE` | Bedingung | Ja | Jump If Less/Equal: wenn ACC <= 0, springe |
| `JZE` | Bedingung | Ja | Jump If Zero: wenn ACC == 0, springe |
| `JNZ` | Bedingung | Ja | Jump If Not Zero: wenn ACC != 0, springe |

**Operand-Formate**:
- Direkt: `03 LDA 05` (Wert aus Speicherzelle 05)
- Indirekt: `03 LDA (05)` (Wert aus Speicherzelle mit Adresse von Zelle 05)
- Absolut: `03 LDA #42` (direkter Wert 42, nur für LDA/ADD/SUB/MUL)

---

## ⚠️ Fehlerbehandlung

Fehlerausgabe zeigt jetzt:

```
▶ ErrorType: Kurze Fehlerbeschreibung
↓ Klick zum Expandieren
```

Bei Expansion:
```
▼ ErrorType: Vollständige Fehlerbeschreibung mit Details
   {Details Parameter}

Program state before crash:
   00 LDA #5
   01 STA 10
   ...
```

**Häufige Fehler**:
- `SyntaxError`: Ungültige Syntax oder Struktur
- `TypeError`: Falsche Datentypen
- `ValueError`: Ungültige Werte
- `StopIteration`: Zu viele Sprünge (Endlosschleife)
- `StopExecution`: Programmlänge überschritten

---

## 👤 Autor

Basierend auf dem ursprünglichen Assemblitor-Projekt von Blyfh (https://github.com/Blyfh/Assemblitor)

---

## 📌 Hinweise

Diese PR bricht keine existierenden Funktionen und ist vollständig abwärtskompatibel. Benutzer können die neuen Features optional nutzen oder weiterhin die alte Eingabemethode verwenden.
