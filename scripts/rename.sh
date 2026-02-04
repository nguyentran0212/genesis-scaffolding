#!/bin/bash

# --- CONFIGURATION ---
OLD_NAME="myproject"
NEW_NAME=$1
SCRIPT_NAME=$(basename "$0")

if [ -z "$NEW_NAME" ]; then
    echo "Usage: ./scripts/$SCRIPT_NAME new-name"
    exit 1
fi

# Create underscore versions
OLD_UNDERSCORE=${OLD_NAME//-/_}
NEW_UNDERSCORE=${NEW_NAME//-/_}

echo "Step 1: Renaming directories and files..."

# Use -path and -prune to skip .git and this script itself
# We use -depth to ensure we rename children before parents
find . -depth \
    \( -path "./.git" -o -name "$SCRIPT_NAME" \) -prune \
    -o -name "*$OLD_NAME*" -exec bash -c '
        new_file=$(echo "$1" | sed "s/'$OLD_NAME'/'$NEW_NAME'/g")
        mv "$1" "$new_file"
    ' _ {} \;

find . -depth \
    \( -path "./.git" -o -name "$SCRIPT_NAME" \) -prune \
    -o -name "*$OLD_UNDERSCORE*" -exec bash -c '
        new_file=$(echo "$1" | sed "s/'$OLD_UNDERSCORE'/'$NEW_UNDERSCORE'/g")
        mv "$1" "$new_file"
    ' _ {} \;

echo "Step 2: Replacing text inside files..."

# Use grep to find files containing the strings, excluding binary/git/lock files
# Then run sed only on those files
find . -type f \
    -not -path "./.git/*" \
    -not -name "$SCRIPT_NAME" \
    -not -name "uv.lock" \
    -exec sed -i "s/$OLD_UNDERSCORE/$NEW_UNDERSCORE/g" {} +

find . -type f \
    -not -path "./.git/*" \
    -not -name "$SCRIPT_NAME" \
    -not -name "uv.lock" \
    -exec sed -i "s/$OLD_NAME/$NEW_NAME/g" {} +

echo "Step 3: Refreshing environment..."
rm -rf .venv
uv sync

echo "Done! Renamed $OLD_NAME ($OLD_UNDERSCORE) to $NEW_NAME ($NEW_UNDERSCORE)."
