#!/usr/bin/env bash
# Install the runic keyboard layout for the current user. No root needed.
set -euo pipefail

SRC="$(cd "$(dirname "$0")" && pwd)/runic"
DEST="${XDG_CONFIG_HOME:-$HOME/.config}/xkb/symbols"

mkdir -p "$DEST"
cp "$SRC" "$DEST/runic"
echo "Installed to $DEST/runic"

if command -v xkbcli >/dev/null && xkbcli compile-keymap --layout runic >/dev/null 2>&1; then
    echo "Layout compiles cleanly."
else
    echo "Warning: layout did not compile. You need libxkbcommon 1.0 or newer." >&2
fi

cat <<'EOF'

Now activate it. User-level layouts do not appear in most desktop
settings GUIs -- that list is built from the system-wide evdev.xml -- so
set it by config or command:

  COSMIC   edit ~/.config/cosmic/com.system76.CosmicComp/v1/xkb_config
           and set  layout: "runic"   (or "no,runic" for two groups)
  Sway     input * xkb_layout "no,runic"
  Hyprland kb_layout = no,runic
  GNOME/KDE these read the system list; either install system-wide (see
           README) or use setxkbmap under X11:  setxkbmap runic

To switch with a key, either add an XKB group toggle option
(grp:alt_shift_toggle) or bind a chord to rune-layout-toggle -- see README.
EOF
