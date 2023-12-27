import os

ESCAPE_FLATPAK = ['flatpak-spawn', '--host']

def is_gnome():
    return "GNOME" in str(os.environ.get("XDG_CURRENT_DESKTOP") or '').upper()

def is_flatpak():
    return os.path.isfile('/.flatpak-info')

if not is_flatpak():
    ESCAPE_FLATPAK = []