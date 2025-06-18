# VoxVibe Monorepo

This repository contains two components:

- `app/` — Python + Qt6 transcription application
- `extension/` — GNOME Shell extension for window focus and pasting



## Prerequisites

1.  **Clone the repository**
2.  **Install Python:** Ensure you have Python 3.11 or newer.
3.  **Install `uv`:** If you don't have `uv` (a fast Python package installer and resolver), install it by following the official instructions at [https://github.com/astral-sh/uv](https://github.com/astral-sh/uv).
4.  **Install `pipx`:** If you don't have `pipx` (a tool for installing and managing Python packages), install it by following the official instructions at [https://pipx.readthedocs.io/en/stable/](https://pipx.readthedocs.io/en/stable/).

## Installation and Setup

This project consists of a GNOME Shell Extension and a Python application. Both need to be set up.

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

### 3. Create Custom Keyboard Shortcut for VoxVibe

To easily launch VoxVibe:

1.  Open **GNOME Settings**.
2.  Navigate to **Keyboard** -> **View and Customize Shortcuts**.
3.  Select **Custom Shortcuts** and click **+**.
4.  In the dialog:
    *   **Name:** `Toggle VoxVibe`
    *   **Command:** `voxvibe`
    *   **Shortcut:** Press your desired key combination (e.g., `Ctrl+Alt+V`).
5.  Click **Add**.

Now, your keyboard shortcut is ready to use.

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
