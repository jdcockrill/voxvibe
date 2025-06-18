# Changelog

All notable changes to VoxVibe will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- First version with working Python transcription app and GNOME Shell extension

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