# Changelog

All notable changes to VoxVibe will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Improved Makefile with distribution and CI/CD support
- GitHub Actions workflow for automated builds and releases
- Contributing guidelines with branching and release strategy
- Tool validation and version management in build system

### Changed
- Enhanced build process with proper dependency checking
- Improved release packaging with installation scripts

## [0.1.0] - 2024-12-XX

### Added
- Initial release of VoxVibe voice dictation application
- Python Qt6-based GUI for audio recording and transcription
- GNOME Shell extension for window management and text pasting
- Whisper AI integration using faster-whisper for speech-to-text
- Audio recording using sounddevice (16kHz, mono)
- DBus communication between Python app and GNOME extension
- Keyboard shortcut support for voice activation
- Automatic window focus restoration and text pasting
- Support for GNOME Shell 48+
- MIT License

### Technical Details
- Python 3.11+ support with PyQt6 GUI framework
- faster-whisper>=1.1.1 for efficient AI transcription
- sounddevice>=0.5.2 for cross-platform audio recording
- numpy>=2.3.0 for numerical operations
- uv package manager for fast dependency management
- Makefile-based build system for coordinated builds

### Project Structure
- `/app` - Python transcription application
- `/extension` - GNOME Shell extension
- Monorepo structure with coordinated builds
- Comprehensive documentation and setup guides

---

## Release Notes Template

When preparing a new release, copy and fill out this template:

```markdown
## [X.Y.Z] - YYYY-MM-DD

### Added
- New features and functionality

### Changed
- Changes to existing functionality
- Performance improvements
- Updated dependencies

### Deprecated
- Features that will be removed in future versions

### Removed
- Features removed in this version

### Fixed
- Bug fixes and corrections

### Security
- Security improvements and fixes
```

## Maintenance Notes

- **Version bumps**: Update version in `app/pyproject.toml` and create corresponding git tag
- **Release process**: Use `make release` to create tagged releases with packages
- **CI/CD**: GitHub Actions automatically builds and publishes releases when tags are pushed
- **Breaking changes**: Always bump major version for breaking changes
- **Dependencies**: Document significant dependency updates in changelog

## Links

- [Keep a Changelog](https://keepachangelog.com/)
- [Semantic Versioning](https://semver.org/)
- [VoxVibe Repository](https://github.com/your-username/voxvibe)