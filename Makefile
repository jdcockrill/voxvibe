# Root Makefile for VoxVibe Monorepo

.PHONY: all app install extension lint clean

# Variables
EXTENSION_UUID := voxvibe@app
EXTENSION_INSTALL_PATH := $(HOME)/.local/share/gnome-shell/extensions/$(EXTENSION_UUID)
PYTHON_APP_DIR := app

all: app install extension
	@echo "\nSetup complete. Please create a keyboard shortcut as described in README.md."

# Target to set up the Python application environment and build it.
app:
	@echo "--> Setting up Python application..."
	@cd $(PYTHON_APP_DIR) && uv sync && uv build

# Target to install the Python application wheel.
install:
	@echo "--> Installing Python application..."
	@cd $(PYTHON_APP_DIR) && uv pip install --force-reinstall dist/*.whl
	@echo "Python application installed. The 'voxvibe' command should now be available."

# Target to install and enable the GNOME Shell extension.
extension:
	@echo "--> Installing GNOME Shell extension..."
	@mkdir -p $(EXTENSION_INSTALL_PATH)
	@cp -r extension/* $(EXTENSION_INSTALL_PATH)/
	@echo "Extension files copied to $(EXTENSION_INSTALL_PATH)"
	@gnome-extensions enable $(EXTENSION_UUID) || echo "Could not enable extension automatically. Please enable 'VoxVibe' in the GNOME Extensions app."
	@echo "IMPORTANT: You may need to reload GNOME Shell (Alt+F2, 'r', Enter on X11; or log out/in on Wayland)."

# Target to run linters.
lint:
	@echo "--> Running linters..."
	@cd $(PYTHON_APP_DIR) && uv run ruff check
	# Add GNOME extension linting if a JS linter is configured.

# Target to clean up build artifacts and installations.
clean:
	@echo "--> Cleaning up..."
	@rm -rf $(PYTHON_APP_DIR)/dist
	@rm -rf $(PYTHON_APP_DIR)/.venv
	@rm -rf $(EXTENSION_INSTALL_PATH)
	@echo "Cleanup complete."
