#!/bin/bash

cd "${HOME}/Documents/github/devault" || exit
git pull

# Python executable
"${HOME}/Documents/github/goodreads2md/.venv/bin/python" \
    # Path to script
    "${HOME}/Documents/github/goodreads2md/scripts/goodreads.py" \
    # Path to Obsidian Library
    "${HOME}/Documents/github/devault/Atlas/Notes/Vaults/Library"

git add .
git commit -m "$(date '+%Y-%m-%dT%H:%M') Update Library files"
git push
