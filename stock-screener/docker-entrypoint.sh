#!/usr/bin/env sh
# docker-entrypoint.sh — runs before streamlit starts.
#
# Responsibilities:
#   1. Wire up /app/data so portfolio.json + session.json persist across
#      container restarts when a volume is mounted at /app/data.
#   2. Seed portfolio.json from the bundled template if missing.
#   3. Exec the main CMD (streamlit run ...).
set -eu

DATA_DIR="/app/data"

# If the user mounted a volume at /app/data, symlink the writable data
# files into it so they survive container recreation. If no volume is
# mounted, /app/data is just a regular dir inside the container and the
# symlinks are still created (pointing into it) — harmless.
mkdir -p "$DATA_DIR"

for f in portfolio.json session.json; do
    target="/app/$f"
    stored="$DATA_DIR/$f"

    # If /app/<file> already exists as a real file (first boot from image),
    # move it into the volume so we don't lose the bundled template.
    if [ -e "$target" ] && [ ! -L "$target" ]; then
        mv "$target" "$stored"
    fi

    # If the file still doesn't exist in the volume, seed portfolio.json
    # with a fresh template; touch session.json.
    if [ ! -e "$stored" ]; then
        case "$f" in
            portfolio.json)
                cat > "$stored" <<'JSON'
{
  "initial_balance": 1000000,
  "balance": 1000000,
  "trades": []
}
JSON
                ;;
            session.json)
                echo '{}' > "$stored"
                ;;
        esac
    fi

    # Create the symlink /app/<file> -> /app/data/<file>
    ln -sf "$stored" "$target"
done

# Hand off to the main CMD
exec "$@"
