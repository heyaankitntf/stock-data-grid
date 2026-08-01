#!/usr/bin/env sh
# docker-entrypoint.sh — runs before streamlit starts.
#
# Responsibilities:
#   1. Wire up /app/data so portfolio.json + session.json persist across
#      container restarts when a volume is mounted at /app/data.
#   2. Seed portfolio.json / session.json from a fresh template if the
#      volume is empty (first boot).
#   3. Exec the main CMD (streamlit run ...).
#
# portfolio.json and session.json are excluded from the image by
# .dockerignore, so they never exist as real files in /app/ — only as
# symlinks into /app/data/.
set -eu

DATA_DIR="/app/data"
mkdir -p "$DATA_DIR"

for f in portfolio.json session.json; do
    target="/app/$f"
    stored="$DATA_DIR/$f"

    # Seed the volume on first boot if the file doesn't exist.
    # (Subsequent boots skip this — the volume retains user data.)
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

    # Create or refresh the symlink /app/<file> -> /app/data/<file>.
    # -f removes an existing symlink/file at $target first.
    # -n avoids dereferencing an existing symlink (idempotent on rerun).
    ln -sfn "$stored" "$target"
done

# Hand off to the main CMD
exec "$@"
