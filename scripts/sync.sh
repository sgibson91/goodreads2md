#!/bin/bash

cd "${HOME}/Documents/github/goodreads2md" || exit
.venv/bin/python scripts/goodreads.py "${HOME}/Documents/github/devault/Atlas/Notes/Vaults/Library"

cd "${HOME}/Documents/github/devault" || exit
git pull
git add .
git commit -m "$(date '+%Y-%m-%dT%H:%M') Update Library files"
git push
