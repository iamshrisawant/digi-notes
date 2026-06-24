#!/bin/bash
set -e

echo "=== Packaging DigiNotes Standalone & Installer ==="

# 1. Clean previous builds
echo "Cleaning old build files..."
rm -rf build dist deb_package *.spec *.deb

# 2. Run PyInstaller to bundle into a single native binary
echo "Compiling with PyInstaller..."
pyinstaller --onefile --noconsole --name "diginotes" --icon "images/app_icon.png" --add-data "images:images" src/main.py

# 3. Create Debian Package Structure
echo "Structuring Debian package..."
mkdir -p deb_package/DEBIAN
mkdir -p deb_package/usr/bin
mkdir -p deb_package/usr/share/applications
mkdir -p deb_package/usr/share/pixmaps

# Copy binary and icon
cp dist/diginotes deb_package/usr/bin/
cp images/app_icon.png deb_package/usr/share/pixmaps/diginotes.png

# Generate DEBIAN/control metadata
cat <<EOT > deb_package/DEBIAN/control
Package: diginotes
Version: 1.0.0
Section: utils
Priority: optional
Architecture: amd64
Maintainer: iamshrisawant
Description: DigiNotes - A beautiful standalone minimalist sticky notes manager.
EOT

# Generate Desktop Entry
cat <<EOT > deb_package/usr/share/applications/diginotes.desktop
[Desktop Entry]
Version=1.0
Type=Application
Name=DigiNotes
Comment=Sleek glassmorphic sticky notes manager
Exec=diginotes
Icon=diginotes
Terminal=false
Categories=Utility;
EOT

# Ensure correct permissions
chmod 755 deb_package/usr/bin/diginotes
chmod 644 deb_package/usr/share/applications/diginotes.desktop
chmod 644 deb_package/usr/share/pixmaps/diginotes.png
chmod 755 deb_package/DEBIAN/control

# 4. Build .deb package
echo "Packaging Debian installer using dpkg-deb..."
dpkg-deb --build deb_package diginotes_1.0.0_amd64.deb

echo "=== Build Complete! Installer generated: diginotes_1.0.0_amd64.deb ==="
