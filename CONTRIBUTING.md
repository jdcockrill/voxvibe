# Contributing to VoxVibe

Thank you for your interest in contributing to VoxVibe! This document provides guidelines for contributing to the project.

## Table of Contents

- [Development Setup](#development-setup)
- [Branching Strategy](#branching-strategy)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Release Strategy](#release-strategy)
- [Code Style](#code-style)
- [Pull Request Process](#pull-request-process)
- [Issue Reporting](#issue-reporting)

## Development Setup

### Prerequisites

- Python 3.11+
- GNOME Shell 48+
- Git
- [uv](https://github.com/astral-sh/uv) (Python package manager)

### Initial Setup

1. **Fork and clone the repository**:
   ```bash
   git clone https://github.com/your-username/voxvibe.git
   cd voxvibe
   ```

2. **Set up development environment**:
   ```bash
   make all
   ```

3. **Verify installation**:
   ```bash
   make check-tools
   make check-version
   ```

4. **Run tests and linting**:
   ```bash
   make lint
   ```

## Branching Strategy

We use a **Git Flow-inspired** branching strategy:

### Branch Types

- **`main`** - Production-ready code, always stable
- **`develop`** - Integration branch for features (optional, we often merge directly to main for small projects)
- **Feature branches** - `feature/issue-number-description`
- **Hotfix branches** - `hotfix/issue-description` for urgent fixes
- **Release branches** - `release/v1.2.3` for release preparation (if needed)

### Branch Naming Convention

- **Feature branches**: `feature/123-add-voice-commands`
- **Bug fixes**: `fix/456-audio-recording-crash`
- **Hotfixes**: `hotfix/critical-security-fix`
- **Documentation**: `docs/update-installation-guide`
- **Refactoring**: `refactor/simplify-audio-pipeline`

### Workflow

1. **Create feature branch** from `main`:
   ```bash
   git checkout main
   git pull origin main
   git checkout -b feature/123-your-feature-name
   ```

2. **Make your changes** with frequent commits:
   ```bash
   git add .
   git commit -m "Add initial voice command structure"
   ```

3. **Keep your branch updated**:
   ```bash
   git checkout main
   git pull origin main
   git checkout feature/123-your-feature-name
   git rebase main
   ```

4. **Push and create PR**:
   ```bash
   git push origin feature/123-your-feature-name
   ```

## Making Changes

### Before You Start

1. **Check existing issues** - Look for related issues or discussions
2. **Create an issue** - For new features or significant changes
3. **Discuss the approach** - Comment on the issue to align on implementation

### Development Process

1. **Create a branch** following the naming convention
2. **Make focused commits** with clear messages
3. **Test your changes** locally:
   ```bash
   make lint          # Run linters
   make dist          # Test build process
   make clean && make all  # Test full installation
   ```
4. **Update documentation** if needed
5. **Add tests** for new functionality (when applicable)

### Commit Message Format

Use conventional commit format:

```
type(scope): brief description

Longer description if needed, explaining the why not the what.

Fixes #123
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `refactor`: Code refactoring and style changes (no logic changes)
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(transcription): add support for multiple languages

- Add language selection dropdown in GUI
- Update Whisper model loading for language-specific models
- Add language preference persistence

Fixes #45

fix(audio): resolve microphone permission issues on Wayland

The audio recorder now properly requests microphone permissions
through the portal system on Wayland sessions.

Fixes #78
```

## Testing

### Local Testing

1. **Lint your code**:
   ```bash
   make lint
   ```

2. **Test the build process**:
   ```bash
   make clean
   make dist
   ```

3. **Test installation**:
   ```bash
   make package
   # Test the generated installation script
   ```

4. **Manual testing**:
   - Test the complete user workflow
   - Test on both X11 and Wayland (if possible)
   - Verify GNOME extension functionality
   - Test edge cases (no microphone, permission denied, etc.)

### Automated Testing

- **CI builds** run automatically on pull requests
- **Release builds** run on tagged versions
- Check the Actions tab for build status

## Release Strategy

### Version Management

- We use **Semantic Versioning** (SemVer): `MAJOR.MINOR.PATCH`
- Version is managed in `app/pyproject.toml`
- Git tags follow the format `v1.2.3`

### Release Types

- **Patch releases** (`1.0.1`) - Bug fixes, small improvements
- **Minor releases** (`1.1.0`) - New features, backward compatible
- **Major releases** (`2.0.0`) - Breaking changes

### Release Process

#### For Maintainers

1. **Prepare release**:
   ```bash
   # Update version in app/pyproject.toml
   # Update CHANGELOG.md
   git add app/pyproject.toml
   git commit -m "chore: bump version to 1.2.3"
   ```

2. **Create and push release**:
   ```bash
   make release  # Creates tag and release package
   git push origin main
   git push origin v1.2.3
   ```

3. **GitHub Actions automatically**:
   - Builds the release packages
   - Creates GitHub release with artifacts
   - Generates release notes

#### Release Schedule

- **Patch releases** - As needed for critical bugs
- **Minor releases** - Monthly or when significant features are ready
- **Major releases** - Rarely, only for breaking changes

## Code Style

### Python Code

- TBD but to start with
- Use **type hints** where appropriate
- Use **ruff** for linting (configured in `pyproject.toml`)

### JavaScript Code (GNOME Extension)

- TBD

### General Guidelines

- **Write clear, self-documenting code**
- **Add comments for complex logic**
- **Use descriptive variable and function names**
- **Keep functions small and focused**
- **Avoid deep nesting** - use early returns

## Pull Request Process

### Before Submitting

1. **Rebase your branch** on the latest `main`
2. **Run all checks** locally:
   ```bash
   make lint
   make dist
   ```
3. **Test your changes** thoroughly
4. **Update documentation** if needed

### PR Requirements

- **Clear title** describing the change
- **Detailed description** explaining:
  - What changes were made
  - Why they were made
  - How to test them
- **Link to related issues** using `Fixes #123` or `Closes #123`
- **Screenshots** for UI changes
- **Testing instructions** for reviewers

### PR Template

```markdown
## Summary
Brief description of changes made.

## Changes Made
- List of specific changes
- Another change
- etc.

## Testing
- [ ] Tested locally on X11
- [ ] Tested locally on Wayland
- [ ] Ran `make lint` successfully
- [ ] Tested installation process

## Related Issues
Fixes #123

## Screenshots (if applicable)
[Add screenshots for UI changes]
```

### Review Process

1. **Automated checks** must pass (CI build, linting)
2. **Code review** by at least one maintainer
3. **Testing** by reviewer when possible
4. **Approval** and merge by maintainer

### After Merge

- **Delete your feature branch**:
  ```bash
  git branch -d feature/123-your-feature-name
  git push origin --delete feature/123-your-feature-name
  ```

## Issue Reporting

### Before Creating an Issue

1. **Search existing issues** for duplicates
2. **Test with the latest version**
3. **Gather system information**:
   - OS and version
   - GNOME Shell version
   - Python version
   - VoxVibe version

### Issue Types

- **🐛 Bug Report** - Something isn't working
- **💡 Feature Request** - New functionality
- **📚 Documentation** - Improve or add documentation
- **❓ Question** - General questions about usage

### Bug Report Template

```markdown
**Describe the bug**
Clear description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. See error

**Expected behavior**
What you expected to happen.

**System Information**
- OS: [e.g. Ubuntu 24.04]
- GNOME Shell version: [e.g. 48.1]
- Python version: [e.g. 3.11.2]
- VoxVibe version: [e.g. 0.1.0]

**Logs**
```
Add relevant logs or error messages
```

**Additional context**
Any other context about the problem.
```

## Getting Help

- **Documentation**: Check the [README](README.md) and project docs
- **Issues**: Search existing issues or create a new one
- **Discussions**: Use GitHub Discussions for general questions
- **Code**: Look at existing code for examples and patterns

## Recognition

Contributors will be recognized in:
- **Release notes** for significant contributions
- **README** contributors section (if we add one)
- **Git commit history** and GitHub insights

Thank you for contributing to VoxVibe! 🎙️✨