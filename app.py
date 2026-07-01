#!/usr/bin/env python3
"""
Hook-Cutter: MP3s an der richtigen Stelle zuschneiden - Intro raus (nur
Refrain/Hook bleibt) ODER Hook raus (nur Intro bleibt, z.B. fuer
"Intro raten"-Runden). Ein Klick, du entscheidest die Richtung.

Nutzung:
    python app.py --input /pfad/zu/mp3s --output /pfad/zu/geschnitten [--port 5050]

Voraussetzung: ffmpeg muss installiert sein (z.B. sudo apt install ffmpeg).
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path

# PyInstaller --noconsole/--windowed builds have no real stdout/stderr,
# which makes bare print() calls crash. Redirect to a null sink in that case.
if getattr(sys, "frozen", False) and sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
    sys.stderr = open(os.devnull, "w")

from flask import Flask, jsonify, request, send_from_directory, render_template


def resource_path(relative: str) -> str:
    """Resolve a path both when running from source and when frozen by PyInstaller."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative)


app = Flask(__name__, template_folder=resource_path("templates"))

INPUT_DIR: Path
OUTPUT_DIR: Path
STATE_FILE: Path

CONFIG_PATH = Path.home() / ".config" / "hookcutter" / "config.json"


def load_config():
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_config(cfg):
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(
        json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def check_ffmpeg():
    """Prueft ob ffmpeg im PATH ist; zeigt bei Bedarf eine freundliche Fehlermeldung."""
    if shutil.which("ffmpeg"):
        return True
    try:
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "ffmpeg fehlt",
            "Hook-Cutter braucht ffmpeg, das aber nicht gefunden wurde.\n\n"
            "Installation unter Windows:\n"
            "  winget install ffmpeg\n"
            "(danach den PC bzw. das Terminal neu starten)\n\n"
            "Installation unter Linux:\n"
            "  sudo apt install ffmpeg",
        )
        root.destroy()
    except Exception:
        print("FEHLER: ffmpeg wurde nicht gefunden. Bitte installieren und erneut starten.")
    return False


def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {}


def save_state(state):
    STATE_FILE.write_text(
        json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def get_mp3_files():
    return sorted(p.name for p in INPUT_DIR.glob("*.mp3"))


def format_timestamp(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/files")
def api_files():
    state = load_state()
    files = get_mp3_files()
    return jsonify(
        [
            {
                "name": f,
                "cut_at": state.get(f, {}).get("cut_at"),
                "mode": state.get(f, {}).get("mode", "from"),
                "skipped": state.get(f, {}).get("skipped", False),
            }
            for f in files
        ]
    )


@app.route("/audio/<path:filename>")
def audio(filename):
    return send_from_directory(INPUT_DIR, filename)


@app.route("/api/cut", methods=["POST"])
def api_cut():
    data = request.get_json(force=True)
    filename = data.get("filename")
    seconds = data.get("seconds")
    mode = data.get("mode", "from")  # "from" = alles VOR der Markierung wegschneiden
                                       # "to"   = alles NACH der Markierung wegschneiden

    if not filename or seconds is None:
        return jsonify({"ok": False, "error": "filename oder seconds fehlt"}), 400
    if mode not in ("from", "to"):
        return jsonify({"ok": False, "error": "ungueltiger mode"}), 400

    src = INPUT_DIR / filename
    if not src.exists():
        return jsonify({"ok": False, "error": f"{filename} nicht gefunden"}), 404

    seconds = max(0.0, float(seconds))
    timestamp = format_timestamp(seconds)
    out_path = OUTPUT_DIR / filename

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if mode == "from":
        # Alles vor der Markierung wegschneiden (Standard: ab Hook)
        cmd = [
            "ffmpeg", "-y",
            "-ss", timestamp,
            "-i", str(src),
            "-c", "copy",
            str(out_path),
        ]
    else:
        # Alles nach der Markierung wegschneiden (z.B. Intro behalten, Hook weg)
        cmd = [
            "ffmpeg", "-y",
            "-i", str(src),
            "-to", timestamp,
            "-c", "copy",
            str(out_path),
        ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        return jsonify({"ok": False, "error": result.stderr[-800:]}), 500

    state = load_state()
    state[filename] = {"cut_at": seconds, "mode": mode, "skipped": False}
    save_state(state)

    return jsonify(
        {"ok": True, "filename": filename, "seconds": seconds, "timestamp": timestamp, "mode": mode}
    )


@app.route("/api/skip", methods=["POST"])
def api_skip():
    """Datei unveraendert in den Output-Ordner uebernehmen (kein Schnitt noetig)."""
    data = request.get_json(force=True)
    filename = data.get("filename")
    if not filename:
        return jsonify({"ok": False, "error": "filename fehlt"}), 400

    src = INPUT_DIR / filename
    if not src.exists():
        return jsonify({"ok": False, "error": f"{filename} nicht gefunden"}), 404

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / filename

    cmd = ["ffmpeg", "-y", "-i", str(src), "-c", "copy", str(out_path)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return jsonify({"ok": False, "error": result.stderr[-800:]}), 500

    state = load_state()
    state[filename] = {"cut_at": None, "skipped": True}
    save_state(state)
    return jsonify({"ok": True, "filename": filename})


@app.route("/api/reset", methods=["POST"])
def api_reset():
    """Schnitt/Skip rueckgaengig machen, damit die Datei neu bearbeitet werden kann."""
    data = request.get_json(force=True)
    filename = data.get("filename")
    state = load_state()
    if filename in state:
        del state[filename]
        save_state(state)
    out_path = OUTPUT_DIR / filename
    if out_path.exists():
        out_path.unlink()
    return jsonify({"ok": True})


def pick_folders_gui(defaults):
    """Zeigt ein natives Fenster zur Ordnerauswahl, merkt sich die letzten Pfade."""
    import tkinter as tk
    from tkinter import filedialog, messagebox

    result = {}
    root = tk.Tk()
    root.title("Hook-Cutter – Ordner wählen")
    root.geometry("580x230")
    root.resizable(False, False)
    try:
        root.iconbitmap(resource_path("assets/icon.ico"))
    except Exception:
        pass

    pad = {"padx": 12, "pady": 6}

    tk.Label(root, text="Ordner mit den Original-MP3s:", anchor="w").grid(
        row=0, column=0, columnspan=2, sticky="w", **pad
    )
    input_var = tk.StringVar(value=defaults.get("input", ""))
    tk.Entry(root, textvariable=input_var, width=58).grid(
        row=1, column=0, sticky="w", padx=(12, 4)
    )

    def browse_input():
        d = filedialog.askdirectory(
            title="Input-Ordner wählen",
            initialdir=input_var.get() or str(Path.home()),
        )
        if d:
            input_var.set(d)

    tk.Button(root, text="Durchsuchen…", command=browse_input).grid(
        row=1, column=1, sticky="w", padx=(4, 12)
    )

    tk.Label(root, text="Ordner für die geschnittenen MP3s:", anchor="w").grid(
        row=2, column=0, columnspan=2, sticky="w", **pad
    )
    output_var = tk.StringVar(value=defaults.get("output", ""))
    tk.Entry(root, textvariable=output_var, width=58).grid(
        row=3, column=0, sticky="w", padx=(12, 4)
    )

    def browse_output():
        d = filedialog.askdirectory(
            title="Output-Ordner wählen",
            initialdir=output_var.get() or str(Path.home()),
        )
        if d:
            output_var.set(d)

    tk.Button(root, text="Durchsuchen…", command=browse_output).grid(
        row=3, column=1, sticky="w", padx=(4, 12)
    )

    def start():
        if not input_var.get() or not output_var.get():
            messagebox.showwarning("Fehlt noch", "Bitte beide Ordner auswählen.")
            return
        result["input"] = input_var.get()
        result["output"] = output_var.get()
        root.destroy()

    def cancel():
        root.destroy()
        sys.exit(0)

    btn_frame = tk.Frame(root)
    btn_frame.grid(row=4, column=0, columnspan=2, pady=24)
    tk.Button(btn_frame, text="Abbrechen", command=cancel, width=12).pack(
        side="left", padx=8
    )
    tk.Button(
        btn_frame, text="Starten", command=start, width=12, bg="#4ade80"
    ).pack(side="left", padx=8)

    root.mainloop()
    return result


def run_app_window(url):
    """Oeffnet die Oberflaeche als eigenstaendiges App-Fenster (kein Browser-Tab noetig).
    Nutzt die im System vorhandene WebView-Komponente (unter Windows: Edge WebView2).
    Blockiert bis das Fenster geschlossen wird."""
    try:
        import webview
    except ImportError:
        webview = None

    if webview is not None:
        try:
            webview.create_window(
                "Hook-Cutter",
                url,
                width=1150,
                height=760,
                min_size=(820, 560),
            )
            webview.start()
            return
        except Exception as e:
            print(f"Eigenes App-Fenster nicht verfuegbar ({e}), weiche auf Browser aus.")

    # Fallback, falls pywebview fehlt oder auf diesem System nicht starten kann
    webbrowser.open(url)
    show_status_window(url)


def show_status_window(url):
    """Fallback-Statusfenster, falls kein eigenes App-Fenster verfuegbar ist."""
    import tkinter as tk

    root = tk.Tk()
    root.title("Hook-Cutter läuft")
    root.geometry("400x160")
    root.resizable(False, False)
    try:
        root.iconbitmap(resource_path("assets/icon.ico"))
    except Exception:
        pass

    tk.Label(root, text="✅ Hook-Cutter läuft im Browser:", font=("", 11, "bold")).pack(
        pady=(20, 4)
    )
    tk.Label(root, text=url, fg="#2563eb").pack()
    tk.Label(
        root,
        text="Dieses Fenster schließen, um das Tool zu beenden.",
        fg="#666",
    ).pack(pady=(16, 0))

    def quit_app():
        root.destroy()
        os._exit(0)

    root.protocol("WM_DELETE_WINDOW", quit_app)
    tk.Button(root, text="Beenden", command=quit_app).pack(pady=16)
    root.mainloop()


def main():
    global INPUT_DIR, OUTPUT_DIR, STATE_FILE

    if not check_ffmpeg():
        sys.exit(1)

    parser = argparse.ArgumentParser(description="Hook-Cutter fuer MP3s")
    parser.add_argument("--input", help="Ordner mit den Original-MP3s")
    parser.add_argument("--output", help="Ordner fuer die geschnittenen MP3s")
    parser.add_argument("--port", type=int, default=5050)
    args = parser.parse_args()

    cfg = load_config()
    used_gui = False

    if args.input and args.output:
        input_path, output_path = args.input, args.output
    else:
        try:
            picked = pick_folders_gui(cfg)
        except Exception as e:
            raise SystemExit(
                f"Ordnerauswahl-Fenster konnte nicht geoeffnet werden ({e}).\n"
                f"Fehlt evtl. 'python3-tk'? Installieren mit: sudo apt install python3-tk\n"
                f"Alternativ per Terminal starten: python app.py --input ... --output ..."
            )
        input_path, output_path = picked["input"], picked["output"]
        used_gui = True

    INPUT_DIR = Path(input_path).expanduser().resolve()
    OUTPUT_DIR = Path(output_path).expanduser().resolve()
    STATE_FILE = OUTPUT_DIR / ".hookcutter_state.json"

    if not INPUT_DIR.exists():
        raise SystemExit(f"Input-Ordner nicht gefunden: {INPUT_DIR}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    cfg["input"] = str(INPUT_DIR)
    cfg["output"] = str(OUTPUT_DIR)
    save_config(cfg)

    files = get_mp3_files()
    print(f"{len(files)} MP3-Dateien gefunden in {INPUT_DIR}")
    print(f"Geschnittene Dateien landen in {OUTPUT_DIR}")

    url = f"http://localhost:{args.port}"

    server_thread = threading.Thread(
        target=lambda: app.run(
            host="0.0.0.0", port=args.port, debug=False, use_reloader=False, threaded=True
        ),
        daemon=True,
    )
    server_thread.start()
    time.sleep(0.8)

    if used_gui:
        # Per Doppelklick gestartet -> eigenstaendiges App-Fenster statt Browser-Tab
        run_app_window(url)
    else:
        webbrowser.open(url)
        print(f"Oeffne im Browser: {url}")
        print("Zum Beenden: Strg+C")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
