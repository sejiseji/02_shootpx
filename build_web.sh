#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BUILD_ROOT="${TMPDIR:-/tmp}/02_shootpx_web_build"
APP_NAME="02_shootpx_web"
APP_DIR="$BUILD_ROOT/$APP_NAME"
APP_FILE="$APP_DIR/$APP_NAME.pyxapp"
HTML_FILE="$APP_DIR/$APP_NAME.html"

rm -rf "$BUILD_ROOT"
mkdir -p "$APP_DIR" "$SCRIPT_DIR/docs"

for path in \
  "audio_system.py" \
  "bitmap_font.py" \
  "boss_system.py" \
  "effects.py" \
  "enemy_system.py" \
  "fireworks.py" \
  "game_models.py" \
  "quaternion_utils.py" \
  "shootpx.py" \
  "shootpx.pyxres"
do
  cp "$SCRIPT_DIR/$path" "$APP_DIR/$path"
done

(
  cd "$APP_DIR"
  pyxel package . shootpx.py
  pyxel app2html "$APP_NAME.pyxapp"
)

python3 - "$HTML_FILE" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
text = path.read_text()
text = text.replace(', gamepad: "enabled"', "")
path.write_text(text)
PY

cp "$HTML_FILE" "$SCRIPT_DIR/index.html"
cp "$HTML_FILE" "$SCRIPT_DIR/docs/index.html"
touch "$SCRIPT_DIR/.nojekyll" "$SCRIPT_DIR/docs/.nojekyll"

echo "Wrote:"
echo "  $SCRIPT_DIR/index.html"
echo "  $SCRIPT_DIR/docs/index.html"
