# Voice Flow Monorepo

This repository contains two components:

- `app/` — Python + Qt6 transcription application
- `extension/` — GNOME Shell extension for window focus and pasting

## Development Environment
- Target OS: Fedora (GNOME + Wayland)
- Python app: see `app/README.md` for setup
- GNOME extension: see `extension/README.md` for setup

## Build & Run Coordination

### Root-level Commands
Use the following commands from the root directory:

- `make app` — Set up and run the Python app
- `make extension` — Build/install the GNOME extension
- `make lint` — Run linters for both components

### Directory Structure
```
voice-flow/
├── app/         # Python transcription app
├── extension/   # GNOME Shell extension
├── README.md    # This file
├── Makefile     # Build coordination
```

## Getting Started
1. Set up Python environment and dependencies in `app/`
2. Develop or install the GNOME extension in `extension/`
3. Use GNOME Custom Keyboard Shortcuts to launch the app

---

See subfolder READMEs for component-specific instructions.
