# Root Makefile for VoxVibe Monorepo

.PHONY: all app install extension lint clean dist package release check-tools check-version help

# Variables
EXTENSION_UUID := voxvibe@voxvibe.app
EXTENSION_INSTALL_PATH := $(HOME)/.local/share/gnome-shell/extensions/$(EXTENSION_UUID)
PYTHON_APP_DIR := app
DIST_DIR := dist
BUILD_DIR := build



# Extract version from pyproject.toml
VERSION := $(shell cd $(PYTHON_APP_DIR) && python -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb'))['project']['version'])")

# Git information
GIT_COMMIT := $(shell git rev-parse --short HEAD)
GIT_TAG := $(shell git describe --tags --exact-match 2>/dev/null || echo "")
GIT_BRANCH := $(shell git rev-parse --abbrev-ref HEAD)

# Default target
all: app install extension
	@echo "\nSetup complete. Please create a keyboard shortcut as described in README.md."

# Help target
help:
	@echo "VoxVibe Makefile Commands:"
	@echo ""
	@echo "Development:"
	@echo "  all          - Setup development environment (app + install + extension)"
	@echo "  app          - Build Python application"
	@echo "  install      - Install Python application locally"
	@echo "  extension    - Install GNOME Shell extension"
	@echo "  lint         - Run code linters"
	@echo "  clean        - Clean build artifacts"
	@echo ""
	@echo "Distribution:"
	@echo "  dist         - Create distribution packages"
	@echo "  package      - Create release package with all components"
	@echo "  release      - Tag and prepare release (requires clean working tree)"
	@echo ""
	@echo "Utilities:"
	@echo "  check-tools  - Verify required tools are installed"
	@echo "  check-version - Display version information"
	@echo "  help         - Show this help message"

# Tool validation
check-tools:
	@echo "--> Checking required tools..."
	@command -v uv >/dev/null 2>&1 || { echo "ERROR: uv is not installed"; exit 1; }
	@command -v pipx >/dev/null 2>&1 || { echo "ERROR: pipx is not installed"; exit 1; }
	@command -v python >/dev/null 2>&1 || { echo "ERROR: python is not installed"; exit 1; }
	@command -v git >/dev/null 2>&1 || { echo "ERROR: git is not installed"; exit 1; }
	@command -v gnome-extensions >/dev/null 2>&1 || { echo "WARNING: gnome-extensions not found (extension installation may fail)"; }
	@echo "All required tools are available."

# Version information
check-version:
	@echo "VoxVibe Version Information:"
	@echo "  Version: $(VERSION)"
	@echo "  Git Commit: $(GIT_COMMIT)"
	@echo "  Git Branch: $(GIT_BRANCH)"
	@echo "  Git Tag: $(if $(GIT_TAG),$(GIT_TAG),<none>)"

# Target to set up the Python application environment and build it.
app: check-tools
	@echo "--> Setting up Python application..."
	@cd $(PYTHON_APP_DIR) && uv sync && uv build

# Target to install the Python application wheel.
install:
	@echo "--> Installing Python application..."
	@pipx install --force app/dist/*.whl
	@echo "Python application installed. The 'voxvibe' command should now be available."

# Target to install and enable the GNOME Shell extension.
extension:
	@echo "--> Installing GNOME Shell extension..."
	@mkdir -p $(EXTENSION_INSTALL_PATH)
	@cp -r extension/* $(EXTENSION_INSTALL_PATH)/
	@echo "Extension files copied to $(EXTENSION_INSTALL_PATH)"
	@gnome-extensions enable $(EXTENSION_UUID) || echo "Could not enable extension automatically. Please enable 'VoxVibe' in the GNOME Extensions app."
	@echo "IMPORTANT: You may need to reload GNOME Shell (Alt+F2, 'r', Enter on X11; or log out/in on Wayland)."

# Enhanced linting with validation
lint: check-tools
	@echo "--> Running linters..."
	@cd $(PYTHON_APP_DIR) && uv run ruff check
	@echo "--> Validating extension metadata..."
	@python -c "import json; json.load(open('extension/metadata.json'))" || { echo "ERROR: Invalid extension metadata.json"; exit 1; }
	@echo "All linting checks passed."

# Distribution targets
dist: clean check-tools lint
	@echo "--> Creating distribution packages..."
	@mkdir -p $(DIST_DIR)
	@cd $(PYTHON_APP_DIR) && uv build
	@echo "Python wheel created in $(PYTHON_APP_DIR)/dist/"

# Create a complete release package
package: dist
	@echo "--> Creating release package..."
	@mkdir -p $(BUILD_DIR)/voxvibe-$(VERSION)
	@mkdir -p $(BUILD_DIR)/voxvibe-$(VERSION)/app
	@mkdir -p $(BUILD_DIR)/voxvibe-$(VERSION)/extension
	
	# Copy Python application wheel
	@cp $(PYTHON_APP_DIR)/dist/*.whl $(BUILD_DIR)/voxvibe-$(VERSION)/app/
	
	# Copy extension files
	@cp -r extension/* $(BUILD_DIR)/voxvibe-$(VERSION)/extension/
	
	# Copy documentation and metadata
	@cp README.md LICENSE Makefile $(BUILD_DIR)/voxvibe-$(VERSION)/
	@cp $(PYTHON_APP_DIR)/README.md $(BUILD_DIR)/voxvibe-$(VERSION)/app/
	
	# Create version info file
	@echo "VoxVibe $(VERSION)" > $(BUILD_DIR)/voxvibe-$(VERSION)/VERSION
	@echo "Git Commit: $(GIT_COMMIT)" >> $(BUILD_DIR)/voxvibe-$(VERSION)/VERSION
	@echo "Build Date: $(shell date -u +"%Y-%m-%d %H:%M:%S UTC")" >> $(BUILD_DIR)/voxvibe-$(VERSION)/VERSION
	
	# Create installation script
	@sed -e 's/{{VERSION}}/$(VERSION)/g' -e 's/{{EXTENSION_UUID}}/$(EXTENSION_UUID)/g' install.sh.template > $(BUILD_DIR)/voxvibe-$(VERSION)/install.sh
	@chmod +x $(BUILD_DIR)/voxvibe-$(VERSION)/install.sh
	
	# Create tarball
	@cd $(BUILD_DIR) && tar -czf voxvibe-$(VERSION).tar.gz voxvibe-$(VERSION)/
	@mv $(BUILD_DIR)/voxvibe-$(VERSION).tar.gz $(DIST_DIR)/
	@echo "Release package created: $(DIST_DIR)/voxvibe-$(VERSION).tar.gz"

# Prepare release (requires clean working tree)
release: check-tools
	@echo "--> Preparing release..."
	@if [ -n "$$(git status --porcelain)" ]; then \
		echo "ERROR: Working tree is not clean. Please commit or stash changes."; \
		exit 1; \
	fi
	@if [ -z "$(GIT_TAG)" ]; then \
		echo "Creating tag v$(VERSION)..."; \
		git tag -a "v$(VERSION)" -m "Release version $(VERSION)"; \
	else \
		echo "Tag $(GIT_TAG) already exists."; \
	fi
	@$(MAKE) package
	@echo "Release v$(VERSION) prepared successfully."
	@echo "To push the release: git push origin v$(VERSION)"

# Enhanced clean target
clean:
	@echo "--> Cleaning up..."
	@rm -rf $(PYTHON_APP_DIR)/dist
	@rm -rf $(PYTHON_APP_DIR)/.venv
	@rm -rf $(EXTENSION_INSTALL_PATH)
	@rm -rf $(DIST_DIR)
	@rm -rf $(BUILD_DIR)
	@echo "Cleanup complete."
