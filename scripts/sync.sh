#!/bin/bash

SOURCE_DIR="/tmp/books/"
DEST_DIR="gdrive:Atlas/Notes/Vaults/Library"

rclone sync -P --checksum --log-file /var/log/rclone.txt "$SOURCE_DIR" "$DEST_DIR"

rm -rf "$SOURCE_DIR"
