# VoxVibe Python Application

This directory contains the Python application for VoxVibe, which handles audio capture, transcription, and communication with the GNOME Shell extension.

## Development

The application is built using Python with `uv` for package management. The main entry point is `voxvibe`, defined in [pyproject.toml](./pyproject.toml) under `[project.scripts]`.

### Key Dependencies

- **PyQt6**: For the application's graphical user interface.
- **faster-whisper**: For efficient audio transcription.
- **sounddevice**: For audio recording.

### Common `uv` Commands

All commands should be run from within the `app/` directory.

- **Install dependencies:**
  ```bash
  uv sync
  ```

- **Run the application (after installation):**
  The `voxvibe` command will be available in your shell after running `make install` from the root directory. For development, you can also run the main module directly:
  ```bash
  uv run python -m voice_flow.main
  ```

- **Run linters:**
  ```bash
  uv run ruff check
  ```

- **Build the application:**
  This creates a distributable wheel package in the `app/target/wheels/` directory.
  ```bash
  uv build
  ```

For full installation instructions, see the main `README.md` in the repository root.
