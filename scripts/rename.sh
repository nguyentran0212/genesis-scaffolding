#!/bin/bash
OLD_NAME="skel"
NEW_NAME=$1 # e.g. "my-app"

if [ -z "$NEW_NAME" ]; then
    echo "Usage: ./rename.sh new-name"
    exit 1
fi

# Create underscore version for Python imports
OLD_UNDERSCORE=${OLD_NAME//-/_}
NEW_UNDERSCORE=${NEW_NAME//-/_}

# 1. Rename files and directories
# Using tac (reverse) to rename children before parents
find . -name "*$OLD_NAME*" | sort -r | while read -r file; do
    new_file=$(echo "$file" | sed "s/$OLD_NAME/$NEW_NAME/g")
    mv "$file" "$new_file"
done

# 2. Replace strings in files
# First, replace underscore versions (imports/packages)
find . -type f -not -path '*/.*' -exec sed -i "s/$OLD_UNDERSCORE/$NEW_UNDERSCORE/g" {} +
# Second, replace dash versions (toml names)
find . -type f -not -path '*/.*' -exec sed -i "s/$OLD_NAME/$NEW_NAME/g" {} +

# 3. Cleanup
rm -rf .venv uv.lock
uv sync
