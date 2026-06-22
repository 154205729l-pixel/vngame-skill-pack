#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
SKILL_DIR="$CODEX_HOME/skills/vngame"

mkdir -p "$CODEX_HOME/skills"
rm -rf "$SKILL_DIR"
cp -R "$ROOT/skills/vngame" "$SKILL_DIR"

echo "Installed vngame skill to: $SKILL_DIR"
echo
echo "Recommended environment variable:"
echo "export VNGAME_FACTORY_ROOT=\"$ROOT/h5-story-factory\""
echo
echo "Demo:"
echo "cd \"$ROOT/h5-story-factory/games/demo-worldcup-night\""
echo "python3 tools/storyboard_server.py"
