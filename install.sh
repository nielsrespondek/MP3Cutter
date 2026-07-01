#!/bin/bash
# Einmalig ausfuehren: legt ein Doppelklick-Icon fuer Hook-Cutter an
# (Desktop + Anwendungsmenue), passend zu GNOME auf Ubuntu.
set -e

DIR="$(cd "$(dirname "$0")" && pwd)"
DESKTOP_FILE="$DIR/Hook-Cutter.desktop"

cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Type=Application
Name=Hook-Cutter
Comment=MP3-Intros wegschneiden
Exec=bash -c 'cd "$DIR" && python3 app.py'
Icon=audio-x-generic
Terminal=false
Categories=AudioVideo;
EOF

chmod +x "$DESKTOP_FILE"
chmod +x "$DIR/start.sh"

mkdir -p "$HOME/.local/share/applications"
cp "$DESKTOP_FILE" "$HOME/.local/share/applications/hookcutter.desktop"

if [ -d "$HOME/Desktop" ]; then
    cp "$DESKTOP_FILE" "$HOME/Desktop/Hook-Cutter.desktop"
    chmod +x "$HOME/Desktop/Hook-Cutter.desktop"
    # GNOME als vertrauenswuerdig markieren, falls gio verfuegbar ist
    gio set "$HOME/Desktop/Hook-Cutter.desktop" "metadata::trusted" true 2>/dev/null || true
fi

echo ""
echo "Fertig!"
echo "- Icon 'Hook-Cutter' liegt jetzt auf dem Schreibtisch und im Anwendungsmenue."
echo "- Falls GNOME beim ersten Doppelklick eine Sicherheitswarnung zeigt:"
echo "  Rechtsklick auf das Icon -> 'Starten erlauben' (nur einmalig noetig)."
