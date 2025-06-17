# VoxVibe Monorepo

This repository contains two components:

- `app/` — Python + Qt6 transcription application
- `extension/` — GNOME Shell extension for window focus and pasting

## Prerequisites

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/voxvibe.git # Replace with your repo URL
    cd voxvibe
    ```
2.  **Install Python:** Ensure you have Python 3.11 or newer.
3.  **Install `uv`:** If you don't have `uv` (a fast Python package installer and resolver), install it by following the official instructions at [https://github.com/astral-sh/uv](https://github.com/astral-sh/uv).

## Installation and Setup

This project consists of a GNOME Shell Extension and a Python application. Both need to be set up.

### Recommended Setup (using `make`)

The easiest way to install both the extension and the application is to use the provided `Makefile` from the root of the repository:

```bash
make all
```

This single command will:
1.  Install and enable the GNOME Shell Extension.
2.  Set up the Python environment, build the application, and install it.

After running `make all`, you may need to reload GNOME Shell (log out/in on Wayland, or `Alt+F2` + `r` on X11). Then, proceed to the keyboard shortcut setup.

### Manual Installation

If you prefer to install the components manually, follow these steps.

#### 1. GNOME Shell Extension Installation

1.  **Identify Extension UUID:** The UUID is `voxvibe@example.com`.
2.  **Install Files:**
    ```bash
    mkdir -p ~/.local/share/gnome-shell/extensions/voxvibe@example.com
    cp -r extension/* ~/.local/share/gnome-shell/extensions/voxvibe@example.com/
    ```
3.  **Reload & Enable:** Reload GNOME Shell and then enable the extension:
    ```bash
    gnome-extensions enable voxvibe@example.com
    ```

#### 2. VoxVibe Application Installation

1.  **Build the App:**
    ```bash
    cd app
    uv sync
    uv build
    ```
2.  **Install the App:**
    ```bash
    uv pip install target/wheels/*.whl --force-reinstall
    cd ..
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

### Makefile Commands
Use these `make` commands from the project root:

- `make app`: Sets up the Python app's environment and builds it (runs `uv sync && uv build` in `app/`). After this, you can install the app using `uv pip install app/target/wheels/*.whl`.
- `make extension`: Currently, this provides guidance. (See "Suggested Improvements" below for enhancing this).
- `make lint`: Runs linters for the Python app.

### Directory Structure
```
voxvibe/
├── app/         # Python transcription app (source, pyproject.toml)
├── extension/   # GNOME Shell extension (extension.js, metadata.json)
├── README.md    # This file
├── Makefile     # Build coordination and helper tasks
```

---
For further development details on specific components, you can explore their respective directories.
The `app/README.md` can be used for more detailed notes on Python app development, and `extension/README.md` for extension-specific development notes.
