# VoxVibe GNOME Extension

This directory contains the source code for the GNOME Shell extension.

## Development

The extension is written in JavaScript (`extension.js`) and its metadata is defined in `metadata.json`. The UUID for this extension is `voxvibe@voxvibe.app`.

The extension exposes a DBus interface that the main Python application uses for window focus and pasting text.

### Installation for Development

For detailed user installation instructions, please see the main `README.md` in the root of the repository.

The root `Makefile` now provides a convenient `make extension` target to automate installation for development.

Alternatively, to set it up manually with a symlink:
1. Create a symlink from this directory to the GNOME Shell extensions directory:
   ```bash
   # Make sure to use the absolute path to this directory
   ln -s /path/to/voxvibe/extension ~/.local/share/gnome-shell/extensions/voxvibe@example.com
   ```
2. Reload GNOME Shell (log out/in on Wayland, or `Alt+F2` + `r` on X11).
3. Enable the extension via the Extensions app or `gnome-extensions enable voxvibe@example.com`.
