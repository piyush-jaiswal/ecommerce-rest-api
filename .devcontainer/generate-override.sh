#!/bin/bash
set -euo pipefail # Exit on error, undefined vars, and pipeline failures
IFS=$'\n\t'       # Stricter word splitting

# These paths are already in use, modify them also if required
IGNORE_FILE=".devcontainer/.devcontainer-ignore"
OVERRIDE_FILE=".devcontainer/docker-compose.override.yml"

write_noop() {
	cat >"$OVERRIDE_FILE" <<EOF
services:
  app: {}
EOF
}

# If .devcontainer-ignore doesn't exist or is empty, write a no-op override
if [ ! -f "$IGNORE_FILE" ] || [ ! -s "$IGNORE_FILE" ]; then
	write_noop
	echo ".devcontainer-ignore not found or empty, writing no-op override"
	exit 0
fi

# Validate and collect entries before writing anything
entries=()
while IFS= read -r folder || [[ -n "$folder" ]]; do
	# Trim Windows-style carriage return
	folder="${folder%$'\r'}"

	# Skip blank lines and comments
	[[ -z "$folder" || "$folder" == \#* ]] && continue

	# Reject absolute paths
	if [[ "$folder" == /* ]]; then
		echo "WARNING: Skipping absolute path: '$folder'"
		continue
	fi

	# Reject entries containing ".." segments
	if [[ "$folder" == *..* ]]; then
		echo "WARNING: Skipping path with traversal segment: '$folder'"
		continue
	fi

	entries+=("$folder")
done <"$IGNORE_FILE"

# If no valid entries found after filtering, write a no-op override
if [ ${#entries[@]} -eq 0 ]; then
	write_noop
	echo "No valid entries found in .devcontainer-ignore, writing no-op override"
	exit 0
fi

# All entries are valid — now write the override file
cat >"$OVERRIDE_FILE" <<EOF
services:
  app:
    tmpfs:
EOF

for folder in "${entries[@]}"; do
	echo "      - /workspace/${folder}" >>"$OVERRIDE_FILE"
done

echo "Generated $OVERRIDE_FILE with ${#entries[@]} tmpfs entries"
