#!/bin/bash

# A script to download and install the latest release of VoxVibe.
#
# This script will automatically fetch the latest release from GitHub,
# download the release package, and run the installer.
#
# Usage:
# curl -sSL https://raw.githubusercontent.com/jdcockrill/voxvibe/main/install.sh | bash

set -e

# --- Configuration ---
REPO="jdcockrill/voxvibe"
API_URL="https://api.github.com/repos/$REPO/releases/latest"

# --- Helper Functions ---
function check_dep() {
  if ! command -v "$1" &> /dev/null; then
    echo "Error: Required command '$1' not found. Please install it and try again."
    exit 1
  fi
}

function cleanup() {
  if [ -n "$TMP_DIR" ] && [ -d "$TMP_DIR" ]; then
    echo "Cleaning up..."
    rm -rf "$TMP_DIR"
  fi
}

# --- Main Script ---
echo "Welcome to the VoxVibe installer!"

# Check for required dependencies
check_dep "curl"
check_dep "jq"
check_dep "tar"

# Set up trap for cleanup on exit
trap cleanup EXIT

# Create a temporary directory for the download
TMP_DIR=$(mktemp -d)
echo "Using temporary directory: $TMP_DIR"

# Get the download URL for the latest release asset
echo "Fetching latest release information from GitHub..."
DOWNLOAD_URL=$(curl -sSL "$API_URL" | jq -r '.assets[] | select(.name | endswith(".tar.gz")) | .browser_download_url')

if [ -z "$DOWNLOAD_URL" ] || [ "$DOWNLOAD_URL" == "null" ]; then
  echo "Error: Could not find a .tar.gz release asset for the latest release."
  echo "Please check the releases page: https://github.com/$REPO/releases"
  exit 1
fi

echo "Found release asset: $DOWNLOAD_URL"

# Download the release asset
FILENAME=$(basename "$DOWNLOAD_URL")
echo "Downloading latest release: $FILENAME..."
curl -L "$DOWNLOAD_URL" -o "$TMP_DIR/$FILENAME"

# Extract the archive
echo "Extracting release package..."
tar -xzf "$TMP_DIR/$FILENAME" -C "$TMP_DIR"

# Find the extracted directory
EXTRACTED_DIR=$(find "$TMP_DIR" -mindepth 1 -maxdepth 1 -type d)
if [ ! -d "$EXTRACTED_DIR" ]; then
    echo "Error: Could not find the extracted directory."
    exit 1
fi

echo "Found extracted directory: $EXTRACTED_DIR"

# Navigate into the extracted directory and run the installer
INSTALL_SCRIPT="$EXTRACTED_DIR/install.sh"
if [ ! -f "$INSTALL_SCRIPT" ]; then
  echo "Error: install.sh not found in the release package."
  exit 1
fi

echo "Running the installer from the release package..."
cd "$EXTRACTED_DIR"
bash ./install.sh

echo "Installation complete! VoxVibe should now be installed."
echo "Thank you for using VoxVibe!"

exit 0
