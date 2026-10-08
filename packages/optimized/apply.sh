#!/usr/bin/env bash
# Aplica este perfil a Clawd Desktop
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONF="$HOME/.config/clawd"; mkdir -p "$CONF"
cp "$DIR/preset.env" "$CONF/profile.env"
echo "Perfil guardado en $CONF/profile.env:"
grep -vE '^\s*#|^\s*$' "$CONF/profile.env" | sed 's/^/  /'
U="$HOME/.config/systemd/user/claude-mascot.service"
if [ -f "$U" ]; then
  sed -i '/^Environment=MASCOT_/d' "$U"
  grep -q EnvironmentFile "$U" || sed -i '/^\[Service\]/a EnvironmentFile=-%h/.config/clawd/profile.env' "$U"
  systemctl --user daemon-reload 2>/dev/null || true
  systemctl --user restart claude-mascot.service 2>/dev/null || true
  echo "Clawd reiniciada con este perfil."
else
  echo "Instala Clawd con packages/suite/install.sh y vuelve a aplicar el perfil."
fi
