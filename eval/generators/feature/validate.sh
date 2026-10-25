#!/bin/bash
# usage: validate.sh <task_dir> [overlay_dir]
T="$1"; O="$2"
W=$(mktemp -d "${TMPDIR:-/tmp}/ambition-validate.XXXXXX")
cp -R "$T/fixture/." "$W/"
if [ -n "$O" ]; then cp -R "$O/." "$W/"; fi
python3 -I "$T/judge/judge.py" "$W"
rm -rf "$W"
