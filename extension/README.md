# Voice Flow GNOME Extension

This directory contains the GNOME Shell extension for Voice Flow.

## Setup

1. Develop extension JS and metadata here.
2. For manual install:
   - Symlink/copy this folder to `~/.local/share/gnome-shell/extensions/voice-flow@yourdomain.com/`
   - Press Alt+F2, type `r`, and hit Enter to reload GNOME Shell (on X11; on Wayland, log out/in).
   - Enable the extension via GNOME Extensions app or `gnome-extensions enable voice-flow@yourdomain.com`

## Development
- Exposes a DBus interface for window focus and pasting.
- See main repo README for build/run coordination.

## TODO
- Scaffold extension files
- Implement DBus interface
