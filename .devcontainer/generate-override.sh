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

	# Drop trailing slashes so the entry can be type-checked
	while [[ "$folder" == */ && "$folder" != "/" ]]; do
		folder="${folder%/}"
	done

	entries+=("$folder")
done <"$IGNORE_FILE"

# If no valid entries found after filtering, write a no-op override
if [ ${#entries[@]} -eq 0 ]; then
	write_noop
	echo "No valid entries found in .devcontainer-ignore, writing no-op override"
	exit 0
fi

# Classify each entry by its type on the host:
#   directories      -> masked with an empty tmpfs (writable, writes are not retained)
#   regular files    -> masked with a read-only /dev/null bind mount (tmpfs cannot be mounted on a file)
#   anything else    -> skipped, as it cannot be masked safely
tmpfs_entries=()
masked_files=()
for folder in "${entries[@]}"; do
	if [[ -d "$folder" ]]; then
		tmpfs_entries+=("/workspace/${folder}")
	elif [[ -f "$folder" ]]; then
		masked_files+=("${folder}")
	elif [[ -e "$folder" || -L "$folder" ]]; then
		echo "WARNING: Skipping unsupported file type: '$folder'"
	else
		# Not present on the host, nothing to mask
		echo "WARNING: Skipping path not found on host: '$folder'"
	fi
done

# If nothing can be masked, write a no-op override
if [ ${#tmpfs_entries[@]} -eq 0 ] && [ ${#masked_files[@]} -eq 0 ]; then
	write_noop
	echo "No maskable entries found in .devcontainer-ignore, writing no-op override"
	exit 0
fi

# All entries are valid — now write the override file
{
	echo "services:"
	echo "  app:"
	if [ ${#tmpfs_entries[@]} -gt 0 ]; then
		echo "    tmpfs:"
		for path in "${tmpfs_entries[@]}"; do
			echo "      - ${path}"
		done
	fi
	if [ ${#masked_files[@]} -gt 0 ]; then
		echo "    volumes:"
		for file in "${masked_files[@]}"; do
			echo "      - /dev/null:/workspace/${file}:ro"
		done
	fi
} >"$OVERRIDE_FILE"

echo "Generated $OVERRIDE_FILE with ${#tmpfs_entries[@]} tmpfs entries and ${#masked_files[@]} masked files"
