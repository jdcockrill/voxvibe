#!/usr/bin/env bash

set -euo pipefail

# Constants
readonly EXTENSION_UUID="voxvibe@voxvibe.app"
readonly DEPENDENCIES=("pipx" "systemctl" "gnome-extensions" "glib-compile-schemas")
readonly GUM_REQUIRED="gum"

# Validate extension UUID format for security
if [[ ! "$EXTENSION_UUID" =~ ^[a-zA-Z0-9_-]+@[a-zA-Z0-9_.-]+\.[a-zA-Z]{2,}$ ]]; then
    echo "Error: Invalid extension UUID format: $EXTENSION_UUID"
    exit 1
fi

# Color constants (from cursor wizard)
readonly CLR_SCS="#16FF15"    # Success - bright green
readonly CLR_INF="#0095FF"    # Info - blue
readonly CLR_BG="#131313"     # Background - dark
readonly CLR_PRI="#6B30DA"    # Primary - purple
readonly CLR_ERR="#FB5854"    # Error - red
readonly CLR_WRN="#FFDA33"    # Warning - yellow
readonly CLR_LGT="#F9F5E2"    # Light - cream

# Variables
VERSION=""
VOXVIBE_PATH=""
GUM_AVAILABLE=false

# Extract version from VERSION file (required)
if [ ! -f "VERSION" ]; then
    echo "Error: VERSION file not found. This installer requires a VERSION file."
    exit 1
fi
VERSION=$(head -n 1 VERSION | sed 's/VoxVibe //')

# Validate version format (semantic versioning)
if [[ ! "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "Error: Invalid version format in VERSION file. Expected format: X.Y.Z"
    echo "Found: '$VERSION'"
    exit 1
fi

# Detect if gum is available
command -v gum >/dev/null 2>&1 && GUM_AVAILABLE=true

# Utility Functions
nostyle() {
    echo "$1" | sed -r 's/\x1B\[[0-9;]*[a-zA-Z]//g'
}

logg() {
    local TYPE="$1" MSG="$2"
    local SYMBOL="" COLOR="" LABEL="" BGCOLOR="" FG=""
    
    case "$TYPE" in
        error) SYMBOL="$(echo -e "\n ✖")" COLOR="$CLR_ERR" LABEL=" ERROR " BGCOLOR="$CLR_ERR" FG="--foreground=$CLR_BG" ;;
        info) SYMBOL=" »" COLOR="$CLR_INF" ;;
        prompt) SYMBOL=" ▶" COLOR="$CLR_PRI" ;;
        star) SYMBOL=" ◆" COLOR="$CLR_WRN" ;;
        success) SYMBOL=" ✔" COLOR="$CLR_SCS" ;;
        warn) SYMBOL="$(echo -e "\n ◆")" COLOR="$CLR_WRN" LABEL=" WARNING " BGCOLOR="$CLR_WRN" FG="--foreground=$CLR_BG" ;;
        *) echo "$MSG"; return ;;
    esac
    
    if [ "$GUM_AVAILABLE" = true ]; then
        # Build the styled message components separately to avoid flag conflicts
        local styled_symbol=$(gum style --foreground="$COLOR" "$SYMBOL")
        local styled_message=$(gum style "$MSG")
        
        if [ -n "$LABEL" ]; then
            local styled_label=$(gum style --bold --background="$BGCOLOR" $FG "$LABEL")
            echo "$styled_symbol $styled_label $styled_message"
        else
            echo "$styled_symbol $styled_message"
        fi
    else
        echo "${TYPE^^}: $MSG"
    fi
    return 0
}

spinner() {
    local title="$1" command="$2"
    if [ "$GUM_AVAILABLE" = true ]; then
        gum spin --spinner "dot" --spinner.foreground="$CLR_SCS" --title "$(gum style --bold "$title")" -- bash -c "$command"
    else
        local chars="|/-\\" i=0
        printf "%s " "$title"
        bash -c "$command" &
        local pid=$!
        while kill -0 $pid 2>/dev/null; do 
            printf "\r%s %c" "$title" "${chars:i++%${#chars}}"
            sleep 0.1
        done
        printf "\r\033[K"
    fi
}

# Security: Validate file paths to prevent path traversal attacks
validate_path() {
    local path="$1"
    local expected_prefix="$2"
    
    # Resolve path to absolute path
    local resolved_path
    resolved_path=$(readlink -f "$path" 2>/dev/null || echo "$path")
    
    # Check if path starts with expected prefix
    if [[ "$resolved_path" != "$expected_prefix"* ]]; then
        return 1
    fi
    
    return 0
}

show_banner() {
    clear
    if [ "$GUM_AVAILABLE" = true ]; then
        gum style --border double --border-foreground="$CLR_PRI" --margin "1 0 2 2" --padding "1 3" --align center --foreground="$CLR_LGT" --background="$CLR_BG" "$(echo -e "🎤 Welcome to VoxVibe Setup! 🎉\n 📡 Effortlessly install and configure voice dictation. 🔧")"
    else
        echo ""
        echo "======================================="
        echo "🎤 Welcome to VoxVibe Setup! 🎉"
        echo "📡 Voice dictation installation wizard"
        echo "======================================="
        echo ""
    fi
}

show_balloon() {
    if [ "$GUM_AVAILABLE" = true ]; then
        gum style --border double --border-foreground="$CLR_PRI" --margin "1 2" --padding "1 1" --align center --foreground="$CLR_LGT" "$1"
    else
        echo "🎈 $1"
    fi
}

check_dependencies() {
    local missing_deps=()
    
    logg info "Checking system dependencies..."
    
    for dep in "${DEPENDENCIES[@]}"; do
        if ! command -v "$dep" >/dev/null 2>&1; then
            missing_deps+=("$dep")
        fi
    done
    
    if [ ${#missing_deps[@]} -gt 0 ]; then
        logg error "Missing required dependencies: ${missing_deps[*]}"
        logg info "Please install missing dependencies and try again."
        logg info "On Ubuntu/Debian, try: sudo apt install ${missing_deps[*]}"
        return 1
    fi
    
    logg success "All required dependencies are available!"
    return 0
}

check_existing_installation() {
    local pipx_installed=false
    local service_installed=false
    local extension_installed=false
    
    # Check if pipx package is installed
    if pipx list 2>/dev/null | grep -q "voxvibe"; then
        pipx_installed=true
    fi
    
    # Check if systemd service exists
    if [ -f "$HOME/.config/systemd/user/voxvibe.service" ]; then
        service_installed=true
    fi
    
    # Check if extension is installed
    if [ -d "$HOME/.local/share/gnome-shell/extensions/$EXTENSION_UUID" ]; then
        extension_installed=true
    fi
    
    # Return true if any component is installed
    if [ "$pipx_installed" = true ] || [ "$service_installed" = true ] || [ "$extension_installed" = true ]; then
        return 0
    else
        return 1
    fi
}

install_python_app() {
    logg prompt "Installing VoxVibe Python application..."
    
    # Validate wheel file exists
    if ! ls app/*.whl >/dev/null 2>&1; then
        logg error "No wheel file found in app/ directory"
        return 1
    fi
    
    if ! spinner "Installing with pipx" "pipx install app/*.whl"; then
        logg error "Failed to install VoxVibe Python package"
        return 1
    fi
    
    # Get the actual installation path from pipx
    VOXVIBE_PATH=$(which voxvibe)
    if [ -z "$VOXVIBE_PATH" ]; then
        logg error "Could not determine voxvibe installation path"
        return 1
    fi
    
    VOXVIBE_PATH="${VOXVIBE_PATH/#\~/$HOME}"
    logg success "VoxVibe Python application installed successfully!"
    return 0
}

install_systemd_service() {
    logg prompt "Setting up systemd user service..."
    
    local install_service=true
    
    if [ -f "$HOME/.config/systemd/user/voxvibe.service" ]; then
        logg info "Existing systemd service configuration found."
        if [ "$GUM_AVAILABLE" = true ]; then
            if gum confirm "Do you want to overwrite the existing service configuration?"; then
                logg info "Updating systemd service configuration..."
                install_service=true
            else
                logg info "Keeping existing systemd service configuration."
                install_service=false
            fi
        else
            read -p "Do you want to overwrite the existing service configuration? (y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                logg info "Updating systemd service configuration..."
                install_service=true
            else
                logg info "Keeping existing systemd service configuration."
                install_service=false
            fi
        fi
    fi
    
    if [ "$install_service" = true ]; then
        mkdir -p "$HOME/.config/systemd/user"
        cat > "$HOME/.config/systemd/user/voxvibe.service" << EOF
[Unit]
Description=VoxVibe Voice Dictation Service
After=graphical-session.target

[Service]
Type=simple
ExecStart=$VOXVIBE_PATH
Restart=on-failure
StandardOutput=journal
StandardError=journal
SyslogIdentifier=voxvibe

[Install]
WantedBy=default.target
EOF
        logg success "Systemd service configuration created!"
    fi
    
    # Reload systemd and enable service
    if spinner "Reloading systemd daemon" "systemctl --user daemon-reload"; then
        logg success "Systemd daemon reloaded"
    fi
    
    if spinner "Enabling VoxVibe service" "systemctl --user enable voxvibe.service"; then
        logg success "VoxVibe service enabled for startup"
    fi
    
    return 0
}

install_gnome_extension() {
    logg prompt "Installing GNOME Shell extension..."
    
    # Validate source directory exists
    if [ ! -d "extension" ]; then
        logg error "Extension source directory not found"
        return 1
    fi
    
    # Stop and disable extension first if it exists
    gnome-extensions disable "$EXTENSION_UUID" 2>/dev/null || true
    
    # Install extension files
    local extension_dir="$HOME/.local/share/gnome-shell/extensions/$EXTENSION_UUID"
    
    # Validate target directory path for security
    if ! validate_path "$extension_dir" "$HOME/.local/share/gnome-shell/extensions/"; then
        logg error "Invalid extension directory path detected"
        return 1
    fi
    
    mkdir -p "$extension_dir"
    if spinner "Copying extension files" "cp -r extension/* \"$extension_dir/\""; then
        logg success "Extension files installed"
    else
        logg error "Failed to copy extension files"
        return 1
    fi
    
    # Install GNOME schema if it exists
    if [ -f "extension/org.gnome.shell.extensions.voxvibe.gschema.xml" ]; then
        logg info "Installing GNOME schema..."
        local schema_dir="$HOME/.local/share/glib-2.0/schemas"
        mkdir -p "$schema_dir"
        cp extension/org.gnome.shell.extensions.voxvibe.gschema.xml "$schema_dir/"
        if spinner "Compiling GLib schemas" "glib-compile-schemas \"$schema_dir\""; then
            logg success "GNOME schema compiled successfully"
        else
            logg warn "Could not compile schemas - extension may not work properly"
        fi
    fi
    
    # Enable extension
    if spinner "Enabling GNOME extension" "gnome-extensions enable '$EXTENSION_UUID'"; then
        logg success "GNOME extension enabled successfully"
    else
        logg warn "Could not enable extension automatically"
        logg info "Please enable 'VoxVibe' in the GNOME Extensions app"
    fi
    
    return 0
}

start_and_verify() {
    logg prompt "Starting VoxVibe service and verifying installation..."
    
    # Start the systemd service
    if spinner "Starting VoxVibe service" "systemctl --user start voxvibe.service"; then
        logg success "VoxVibe service started"
    else
        logg warn "Could not start VoxVibe service"
    fi
    
    # Verify systemd service
    sleep 2
    if systemctl --user is-active --quiet voxvibe.service; then
        logg success "✓ VoxVibe systemd service is running"
    else
        logg warn "⚠ VoxVibe systemd service is not running"
        logg info "Check logs with: journalctl --user -u voxvibe.service"
    fi
    
    # Verify GNOME extension
    if gnome-extensions list --enabled 2>/dev/null | grep -q "$EXTENSION_UUID"; then
        logg success "✓ VoxVibe GNOME extension is enabled"
    else
        logg warn "⚠ VoxVibe GNOME extension is not enabled"
        logg info "Enable manually with: gnome-extensions enable $EXTENSION_UUID"
        logg info "Or reload GNOME Shell (Alt+F2 -> r) and try again"
    fi
    
    return 0
}

remove_existing_installation() {
    logg prompt "Updating existing VoxVibe installation..."
    
    # Stop systemd service (but don't disable or remove config)
    systemctl --user stop voxvibe.service 2>/dev/null || true
    
    # Remove pipx package
    if spinner "Removing existing Python package" "pipx uninstall voxvibe 2>/dev/null || true"; then
        logg success "Previous Python package removed"
    fi
    
    # Disable and remove extension
    gnome-extensions disable "$EXTENSION_UUID" 2>/dev/null || true
    local extension_path="$HOME/.local/share/gnome-shell/extensions/$EXTENSION_UUID"
    # Validate path before removal for security
    if [[ "$extension_path" =~ ^/home/.*/\.local/share/gnome-shell/extensions/voxvibe@voxvibe\.app$ ]]; then
        if spinner "Removing extension files" "rm -rf \"$extension_path\""; then
            logg success "Previous extension files removed"
        fi
    else
        logg error "Invalid extension path detected, skipping removal for security"
        return 1
    fi
    
    # Remove schema if it exists
    rm -f "$HOME/.local/share/glib-2.0/schemas/org.gnome.shell.extensions.voxvibe.gschema.xml"
    if [ -d "$HOME/.local/share/glib-2.0/schemas/" ]; then
        if ! glib-compile-schemas "$HOME/.local/share/glib-2.0/schemas/" 2>/dev/null; then
            logg warn "Could not recompile GLib schemas after removal"
        fi
    fi
    
    logg success "Existing installation components updated"
}

complete_installation() {
    install_python_app || return 1
    install_systemd_service || return 1  
    install_gnome_extension || return 1
    start_and_verify || return 1
    
    show_balloon "$(echo -e "🎉 VoxVibe $VERSION installed successfully! 🎈\n🎤 Ready to start voice dictation? Let's configure your hotkey! 💻")"
    
    logg success "Installation complete!"
    logg info "Next steps:"
    logg info "- Create a keyboard shortcut in GNOME Settings -> Keyboard -> Custom Shortcuts"
    logg info "- Set command: voxvibe"  
    logg info "- Assign your preferred hotkey (e.g., Ctrl+Alt+V)"
    
    return 0
}

menu() {
    local option
    show_banner
    
    while true; do
        if [ "$GUM_AVAILABLE" = true ]; then
            local full_install=$(gum style --foreground="$CLR_LGT" --bold "Complete Installation (recommended)")
            local update_install=$(gum style --foreground="$CLR_LGT" --bold "Update Existing Installation")
            local python_only=$(gum style --foreground="$CLR_LGT" --bold "Install Python App Only")
            local extension_only=$(gum style --foreground="$CLR_LGT" --bold "Install GNOME Extension Only") 
            local service_only=$(gum style --foreground="$CLR_LGT" --bold "Install Systemd Service Only")
            local verify_install=$(gum style --foreground="$CLR_LGT" --bold "Verify Installation Status")
            local _exit=$(gum style --foreground="$CLR_LGT" --italic "Exit")
            
            option=$(echo -e "$full_install\n$update_install\n$python_only\n$extension_only\n$service_only\n$verify_install\n$_exit" | gum choose --header "🎤 Choose your VoxVibe setup option:" --header.margin="0 0 0 2" --header.border="rounded" --header.padding="0 2 0 2" --header.italic --header.foreground="$CLR_LGT" --cursor=" ➤ " --cursor.foreground="$CLR_ERR" --cursor.background="$CLR_PRI" --selected.foreground="$CLR_LGT" --selected.background="$CLR_PRI")
        else
            echo "🎤 Choose your VoxVibe setup option:"
            echo "1) Complete Installation (recommended)"
            echo "2) Update Existing Installation"
            echo "3) Install Python App Only"
            echo "4) Install GNOME Extension Only"
            echo "5) Install Systemd Service Only"
            echo "6) Verify Installation Status"
            echo "7) Exit"
            read -p "Enter your choice (1-7): " choice
            case $choice in
                1) option="Complete Installation (recommended)" ;;
                2) option="Update Existing Installation" ;;
                3) option="Install Python App Only" ;;
                4) option="Install GNOME Extension Only" ;;
                5) option="Install Systemd Service Only" ;;
                6) option="Verify Installation Status" ;;
                7) option="Exit" ;;
                *) logg error "Invalid choice. Please enter 1-7."; continue ;;
            esac
        fi
        
        case "$(nostyle "$option")" in
            *"Complete Installation"*)
                if check_existing_installation; then
                    logg info "VoxVibe components already installed."
                    if [ "$GUM_AVAILABLE" = true ]; then
                        if gum confirm "Do you want to upgrade to version $VERSION?"; then
                            remove_existing_installation
                            complete_installation
                        fi
                    else
                        read -p "Do you want to upgrade to version $VERSION? (y/N): " -n 1 -r
                        echo
                        if [[ $REPLY =~ ^[Yy]$ ]]; then
                            remove_existing_installation
                            complete_installation
                        fi
                    fi
                else
                    complete_installation
                fi
                ;;
            *"Update Existing"*)
                if check_existing_installation; then
                    remove_existing_installation
                    complete_installation
                else
                    logg warn "No existing installation found. Use 'Complete Installation' instead."
                fi
                ;;
            *"Python App Only"*)
                install_python_app
                ;;
            *"GNOME Extension Only"*)
                install_gnome_extension
                ;;
            *"Systemd Service Only"*)
                if [ -z "$VOXVIBE_PATH" ]; then
                    VOXVIBE_PATH=$(which voxvibe 2>/dev/null || echo "")
                    if [ -z "$VOXVIBE_PATH" ]; then
                        logg error "VoxVibe Python app not found. Install it first."
                        continue
                    fi
                fi
                install_systemd_service
                ;;
            *"Verify Installation"*)
                start_and_verify
                ;;
            *"Exit"*)
                if [ "$GUM_AVAILABLE" = true ]; then
                    if gum confirm "Are you sure you want to exit?" --show-help --prompt.foreground="$CLR_WRN" --selected.background="$CLR_PRI"; then
                        clear
                        gum style --border double --border-foreground="$CLR_PRI" --padding "1 3" --margin "1 2" --align center --background "$CLR_BG" --foreground "$CLR_LGT" "$(echo -e "🎤🎉 Thanks for using VoxVibe Setup!\n\n Happy voice dictating! 🎈\n Your productivity journey starts now! 💜")"
                        echo -e " \n\n "
                        break
                    fi
                else
                    echo "Thanks for using VoxVibe Setup!"
                    break
                fi
                ;;
        esac
        
        if [ "$GUM_AVAILABLE" = true ]; then
            if gum confirm "$(echo -e "\nWould you like to do something else?" | gum style --foreground="$CLR_PRI")" --affirmative="《Back" --negative="✖ Close" --show-help --prompt.foreground="$CLR_WRN" --selected.background="$CLR_PRI"; then
                show_banner
            else
                break
            fi
        else
            read -p "Would you like to do something else? (y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                show_banner
            else
                break
            fi
        fi
    done
}

main() {
    clear
    echo ""
    
    check_dependencies || exit 1
    
    if [ "$GUM_AVAILABLE" = true ]; then
        logg success "Enhanced UI available - using gum for better experience!"
    else
        logg info "For a better experience, install 'gum': https://github.com/charmbracelet/gum"
    fi
    
    spinner "Initializing VoxVibe setup wizard..." "sleep 1"
    menu
}

main
