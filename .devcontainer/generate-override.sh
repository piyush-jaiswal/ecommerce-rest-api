#!/bin/bash

# These paths are already in use, modify them also if required
IGNORE_FILE=".devcontainer/.devcontainer-ignore"
OVERRIDE_FILE=".devcontainer/docker-compose.override.yml"

# If .devcontainer-ignore doesn't exist or is empty, generate a sample file, so devcontainer.json reference doesn't break
if [ ! -f "$IGNORE_FILE" ] || [ ! -s "$IGNORE_FILE" ]; then
	# Write a valid no-op override
	cat >$OVERRIDE_FILE <<EOF
services:
  app: {}
EOF
	echo ".devcontainer-ignore not found or empty, writing no-op override"
	exit 0
fi

cat >$OVERRIDE_FILE <<EOF
services:
  app:
    tmpfs:
EOF

# add paths in IGNORE_FILE to OVERRIDE_FILE
while IFS= read -r folder || [[ -n "$folder" ]]; do
	[[ -z "$folder" || "$folder" == \#* ]] && continue
	echo "      - /workspace/${folder}" >>$OVERRIDE_FILE
done <"$IGNORE_FILE"

echo "Generated $OVERRIDE_FILE"
