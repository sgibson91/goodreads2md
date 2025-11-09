#!/bin/bash

if [[ "$OSTYPE" == "darwin"* ]]; then
    SOURCE_DIR="/tmp/books/"
else
    SOURCE_DIR="${TMPDIR}/books/"
fi

DEST_DIR="${HOME}/Google\ Drive/My\ Drive/devault/Library"

rsync -rvc --delete "${SOURCE_DIR}" "${DEST_DIR}"
