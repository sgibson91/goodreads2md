#!/bin/bash

SOURCE_DIR="/tmp/books/"
DEST_DIR="gdrive:devault/Atlas/Notes/Vaults/Library"

rclone sync --checksum "$SOURCE_DIR" "$DEST_DIR"

rm -rf "$SOURCE_DIR"
