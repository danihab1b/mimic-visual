#!/usr/bin/env bash
# ===========================================================================
# entrypoint.sh — flexible CLI/server startup for Mimic-Visual
#
# Usage:
#   docker run visrag                  -> visrag serve (default)
#   docker run visrag render <args>    -> visrag render <args>
#   docker run visrag extract <args>   -> visrag extract <args>
#   docker run visrag chunk <args>     -> visrag chunk <args>
#   docker run visrag embed <args>     -> visrag embed <args>
#   docker run visrag index build      -> visrag index build
#   docker run visrag index info       -> visrag index info
#   docker run visrag reconstruct <id> -> visrag reconstruct <id>
# ===========================================================================
set -euo pipefail

CONFIG="${VISRAG_CONFIG:-/app/visrag.yaml}"

# If no args or first arg is "serve", run the API server
if [ $# -eq 0 ] || [ "$1" = "serve" ]; then
    shift 2>/dev/null || true
    exec python -m visrag.cli.main -c "$CONFIG" serve \
        --index-dir "${INDEX_DIR:-/app/index}" \
        --host "${HOST:-0.0.0.0}" \
        --port "${PORT:-30001}" \
        "$@"
fi

# Otherwise, pass through to visrag CLI
exec python -m visrag.cli.main -c "$CONFIG" "$@"
