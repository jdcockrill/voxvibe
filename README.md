# VoxVibe Monorepo

This repository contains two components:

- `app/` — Python + Qt6 transcription application
- `extension/` — GNOME Shell extension for window focus and pasting

Built with [Claude Code](https://www.anthropic.com/claude-code) and [Windsurf](https://windsurf.com/).

## Prerequisites

1.  **Clone the repository**
2.  **Install Python:** Ensure you have Python 3.11 or newer.
3.  **Install `uv`:** If you don't have `uv` (a fast Python package installer and resolver), install it by following the official instructions at [https://github.com/astral-sh/uv](https://github.com/astral-sh/uv).
4.  **Install `pipx`:** If you don't have `pipx` (a tool for installing and managing Python packages), install it by following the official instructions at [https://pipx.readthedocs.io/en/stable/](https://pipx.readthedocs.io/en/stable/).
5.  **Install PortAudio system dependency:** VoxVibe uses sounddevice which requires PortAudio. Install it using your system's package manager:
    - **Ubuntu/Debian:** `sudo apt install -y portaudio19-dev`
    - **Fedora:** `sudo dnf install portaudio portaudio-devel`
    - **Arch Linux:** `sudo pacman -S portaudio`

Note: `pipx` isn't _strictly_ required. It just makes the creation of the Custom Keyboard Shortcut much simpler.

## Installation and Setup

This project consists of a GNOME Shell Extension and a Python application. Both need to be set up.

### Installation via the Makefile

To install both the Python application and the GNOME Shell extension using the Makefile, follow these steps:

1. **Check prerequisites** (see above): Ensure you have Python 3.11+, `uv` and `pipx` installed.

2. **Run the main setup command:**
    ```bash
    make all
    ```
    This will:
    - Set up the Python application environment and build it (`make app`)
    - Install the Python application locally via `pipx` (`make install`)
    - Install and enable the GNOME Shell extension (`make extension`)

    After completion, you should see a message indicating setup is complete.

3. **Reload GNOME Shell:**
    - On X11: Press <kbd>Alt</kbd> + <kbd>F2</kbd>, type `r`, and press <kbd>Enter</kbd>
    - On Wayland: Log out and log back in

After installation, follow the instructions in the [Create Custom Keyboard Shortcut for VoxVibe](#create-custom-keyboard-shortcut-for-voxvibe) section to set up a convenient way to launch the Python app. You should also see the extension active in GNOME Shell.

### Manual Installation

If you prefer to install the components manually, follow these steps.

#### 1. GNOME Shell Extension Installation

1.  **Install Files:**
    ```bash
    mkdir -p ~/.local/share/gnome-shell/extensions/voxvibe@voxvibe.app
    cp -r extension/* ~/.local/share/gnome-shell/extensions/voxvibe@voxvibe.app/
    ```
2.  **Reload & Enable:** Reload GNOME Shell and then enable the extension:
    ```bash
    gnome-extensions enable voxvibe@voxvibe.app
    ```
    For Wayland, you need to log out and log in again. You should see a microphone icon
    appear in the system tray.

#### 2. VoxVibe Application Installation

You can install the application using `pipx`.

1.  **Build the App:**
    ```bash
    cd app
    uv sync
    uv build
    ```
2.  **Install the App:**
    ```bash
    pipx install app/dist/voxvibe-*.whl
    ```

If you make changes to the application yourself and want to reinstall it, you can use the `--force` flag:
```bash
pipx install --force app/dist/voxvibe-*.whl
```

### Create Custom Keyboard Shortcut for VoxVibe

To easily launch VoxVibe:

1.  Open **GNOME Settings**.
2.  Navigate to **Keyboard** -> **View and Customize Shortcuts**.
3.  Select **Custom Shortcuts** and click **+**.
4.  In the dialog:
    *   **Name:** `VoxVibe`
    *   **Command:** `voxvibe`
    *   **Shortcut:** Press your desired key combination (e.g., `Super+F2`).
5.  Click **Add**.

Now, your keyboard shortcut is ready to use.

Note: if you don't have `pipx` installed, your command will need to be something much longer, such as:

```bash
/path/to/project/app/.venv/bin/voxvibe
```

## Development

### Directory Structure
```
voxvibe/
├── app/         # Python transcription app (source, pyproject.toml)
├── extension/   # GNOME Shell extension (extension.js, metadata.json)
├── README.md    # This file
```

---
For further development details on specific components, you can explore their respective directories.
The `app/README.md` can be used for more detailed notes on Python app development, and `extension/README.md` for extension-specific development notes.

### Release

To release a new version, follow these steps:

1.  **Update Version:** Update the version in `app/pyproject.toml` and `extension/metadata.json`.
2.  **Build Release:** Run `make release` to create the release package.
3.  **Push Release:** Push the release tag to GitHub: `git push origin v$(VERSION)`.
