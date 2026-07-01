# 🎧 Hook-Cutter

Songs nacheinander anhören und mit einem Klick (oder Enter) das Intro
wegschneiden, sodass gleich der Refrain / die Hook kommt. Ideal, um viele
MP3s schnell für Quiz-Runden, DJ-Sets o.ä. vorzubereiten.

Der Schnitt läuft verlustfrei über `ffmpeg -c copy` — dauert pro Datei nur
Sekundenbruchteile, egal wie viele Songs du hast.

## Download (Windows)

👉 Fertige `HookCutter.exe` unter [**Releases**](../../releases) herunterladen —
kein Python nötig.

**Voraussetzung:** [ffmpeg](https://www.gyan.dev/ffmpeg/builds/) muss
installiert und im PATH sein, z. B. per PowerShell:
```
winget install ffmpeg
```
(danach einmal ab- und wieder anmelden bzw. Terminal neu starten, damit PATH
aktualisiert wird)

Beim ersten Start zeigt Windows SmartScreen evtl. eine Warnung
("Unbekannter Herausgeber") — normal bei unsignierten Open-Source-Programmen.
Auf **„Weitere Informationen"** → **„Trotzdem ausführen"** klicken.

## So funktioniert's

1. HookCutter.exe starten
2. Im Fenster den Ordner mit den Original-MP3s und einen Ausgabeordner
   auswählen (wird für's nächste Mal gemerkt)
3. Browser öffnet sich automatisch — Songs spielen nacheinander ab
4. **Leertaste** = Play/Pause, **← →** = ±5s, **↑ ↓** = ±1s zum Feinjustieren
5. **Enter** oder Klick auf „✂️ Hier ist der Hook!" schneidet die Datei ab der
   aktuellen Stelle und springt automatisch zum nächsten Song
6. Kein Intro vorhanden? „Ohne Schnitt übernehmen" klicken

Fortschritt wird gespeichert — du kannst also jederzeit unterbrechen und
später weitermachen.

## Screenshots

_(hier gerne ein, zwei Screenshots der Oberfläche einfügen)_

---

## Für Entwickler / Selbst bauen

### Aus dem Quellcode starten

```bash
pip install -r requirements.txt
python app.py
```

Voraussetzungen: Python 3 mit `tkinter` (unter Linux ggf.
`sudo apt install python3-tk`) und ffmpeg im PATH.

### Windows-exe selbst bauen

```
build.bat
```

baut `dist\HookCutter.exe` lokal (benötigt Python + pip). Alternativ baut es
GitHub Actions automatisch für dich (siehe unten).

### Automatischer Build per GitHub Actions

Bei jedem Push eines Tags im Format `v*` (z. B. `v1.0.0`) baut
[`.github/workflows/build.yml`](.github/workflows/build.yml) automatisch die
`HookCutter.exe` auf einem `windows-latest`-Runner und hängt sie als Asset an
ein neues GitHub Release an. Manuell auslösen geht auch über den
"Run workflow"-Button im Actions-Tab.

```bash
git tag v1.0.0
git push origin v1.0.0
```

### Projektstruktur

```
hookcutter/
├── app.py                    # Flask-Backend + Ordnerauswahl (tkinter)
├── templates/index.html      # Frontend (Player + Schnitt-UI)
├── assets/icon.ico           # App-Icon
├── hookcutter.spec           # PyInstaller-Konfiguration
├── build.bat                 # lokaler Windows-Build
├── start.bat                 # Start aus dem Quellcode (Windows)
├── start.sh / install.sh     # Start bzw. Doppelklick-Icon (Linux/GNOME)
└── .github/workflows/build.yml   # automatischer Windows-Build via CI
```

## Linux (aus dem Quellcode)

```bash
sudo apt install python3-tk ffmpeg
pip install -r requirements.txt
chmod +x install.sh && ./install.sh   # legt ein Doppelklick-Icon an
```

## Lizenz

MIT — siehe [LICENSE](LICENSE)
