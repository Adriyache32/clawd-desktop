#!/usr/bin/env bash
# Clawd - instalador de la mascota de escritorio de Claude Code
set -uo pipefail

APP_NAME="Clawd"
SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="$HOME/.local/bin"
APP="$BIN_DIR/claude-mascot.py"
UNIT_DIR="$HOME/.config/systemd/user"
AUTOSTART_DIR="$HOME/.config/autostart"
UNIT="$UNIT_DIR/claude-mascot.service"
GUM=0; command -v gum >/dev/null 2>&1 && GUM=1
WT=0; command -v whiptail >/dev/null 2>&1 && WT=1

# ---------- UI ----------
title() {
  if [ "$GUM" = 1 ]; then
    gum style --foreground 209 --border rounded --padding "0 2" --margin "1 2" \
      --bold "$1"
  else echo "=== $1 ==="; fi
}
info() {
  if [ "$GUM" = 1 ]; then gum style --foreground 250 --margin "0 2" "$1"
  else echo "$1"; fi
}
menu() { # menu "header" item...
  local header="$1"; shift
  if [ "$GUM" = 1 ]; then
    gum choose --header "$header" --cursor "➜ " --cursor.foreground 209 --selected.foreground 209 "$@"
  elif [ "$WT" = 1 ]; then
    local args=(); local i=1
    for o in "$@"; do args+=("$i" "$o"); i=$((i+1)); done
    whiptail --title "$header" --menu "" 18 76 8 "${args[@]}" 3>&1 1>&2 2>&3
  else
    select o in "$@"; do echo "$o"; break; done
  fi
}
confirm() {
  if [ "$GUM" = 1 ]; then gum confirm --affirmative "Sí" --negative "No" "$1"
  elif [ "$WT" = 1 ]; then whiptail --yesno "$1" 12 70
  else read -rp "$1 [s/N] " a; [[ "$a" =~ ^[sS] ]]; fi
}
ask() {
  if [ "$GUM" = 1 ]; then gum input --placeholder "$2" --prompt "➜ " <<<"${2:-}"
  elif [ "$WT" = 1 ]; then whiptail --inputbox "$1" 10 70 "$2" 3>&1 1>&2 2>&3
  else read -rp "$1 " a; echo "$a"; fi
}
spin() { # spin "title" cmd...
  local t="$1"; shift
  if [ "$GUM" = 1 ]; then gum spin --spinner dot --title "$t" -- "$@"
  else echo "$t"; "$@"; fi
}
pause_ok() { [ "$GUM" = 1 ] && gum style --foreground 209 "✔ $1" || echo "OK: $1"; }

# ---------- sistema ----------
detect_pm() { for c in pacman apt dnf zypper; do command -v "$c" >/dev/null 2>&1 && echo "$c" && return; done; }
pkg_names() {
  case "$(detect_pm)" in
    pacman) echo "python-gobject python-cairo gtk3 xorg-xprintidle playerctl imagemagick xdotool libnotify" ;;
    apt)    echo "python3-gi python3-cairo gir1.2-gtk-3.0 xprintidle playerctl imagemagick xdotool libnotify-bin" ;;
    dnf)    echo "python3-gobject python3-cairo gtk3 xprintidle playerctl ImageMagick xdotool libnotify" ;;
    *)      echo "" ;;
  esac
}
have_deps() { python3 -c "import gi,cairo" >/dev/null 2>&1; }
install_deps() {
  local pm; pm=$(detect_pm); [ -z "$pm" ] && { info "Instala a mano: python-gobject, python-cairo, gtk3, xprintidle, playerctl, imagemagick."; return 1; }
  confirm "Instalo las dependencias con $pm?" || return 1
  local pkgs; pkgs=$(pkg_names)
  case "$pm" in
    pacman) spin "Instalando dependencias…" sudo pacman -S --needed --noconfirm $pkgs ;;
    apt)    spin "Instalando dependencias…" sudo apt-get install -y $pkgs ;;
    dnf)    spin "Instalando dependencias…" sudo dnf install -y $pkgs ;;
  esac
}
have_ollama() { command -v ollama >/dev/null 2>&1; }
install_ollama() {
  confirm "Ollama no está. ¿Lo instalo (script oficial)?" || return 1
  spin "Instalando Ollama…" sh -c 'curl -fsSL https://ollama.com/install.sh | sh'
  systemctl --user enable --now ollama 2>/dev/null || (nohup ollama serve >/dev/null 2>&1 &)
}
ram_gb() { awk '/MemTotal/{printf "%.1f", $2/1048576}' /proc/meminfo; }
recommend() {
  local r; r=$(ram_gb)
  awk -v r="$r" 'BEGIN{ if(r<6)print "0.5b"; else if(r<12)print "1.5b"; else if(r<20)print "3b"; else print "7b" }'
}
model_id() { case "$1" in 0.5b) echo qwen2.5:0.5b;; 1.5b) echo qwen2.5:1.5b;; 2b) echo qwen2.5:3b;; 3b) echo gemma3:4b;; 4b) echo qwen2.5:7b;; esac; }

MODELS=(
  "0.5b · ~0.4 GB RAM · mínimo"
  "1.5b · ~1.0 GB RAM · equilibrado"
  "2b   · ~2.0 GB RAM · buena calidad"
  "3b   · ~3.3 GB RAM · más listo"
  "4b   · ~4.7 GB RAM · el más capaz"
  "Otro · escribir el nombre"
)

choose_model() {
  local rec; rec=$(recommend)
  title "Modelo del cerebro"
  info "RAM de tu PC: $(ram_gb) GB   ·   recomendado: $rec"
  local pick
  pick=$(menu "Elige el modelo (tamaño · RAM · calidad):" "${MODELS[@]}") || return
  local id
  case "$pick" in
    0.5b*) id=qwen2.5:0.5b ;;
    1.5b*) id=qwen2.5:1.5b ;;
    2b*)   id=qwen2.5:3b ;;
    3b*)   id=gemma3:4b ;;
    4b*)   id=qwen2.5:7b ;;
    Otro*) id=$(ask "Nombre del modelo en Ollama (ej: llama3.2:3b):" "qwen2.5:1.5b") ;;
    *) return ;;
  esac
  have_ollama || { info "Necesitas Ollama para descargar modelos."; return; }
  spin "Descargando $id…" ollama pull "$id" && {
    save_model "$id"; pause_ok "Modelo $id listo."; }
}

save_model() {
  [ -f "$UNIT" ] || return
  sed -i "/^Environment=MASCOT_OLLAMA_MODEL/d" "$UNIT"
  sed -i "/^ExecStart=/a Environment=MASCOT_OLLAMA_MODEL=$1" "$UNIT"
  systemctl --user daemon-reload 2>/dev/null || true
}

install_files() {
  mkdir -p "$BIN_DIR" "$UNIT_DIR" "$AUTOSTART_DIR"
  install -m 755 "$SRC_DIR/claude-mascot.py" "$APP"
  local model; model=$(model_id "$(recommend)")
  cat > "$UNIT" <<EOF
[Unit]
Description=Clawd - mascota de escritorio de Claude Code
After=graphical-session.target
PartOf=graphical-session.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 $APP
Environment=MASCOT_OLLAMA_MODEL=$model
PassEnvironment=DISPLAY XAUTHORITY
Restart=on-failure
RestartSec=3

[Install]
WantedBy=default.target
EOF
  cat > "$AUTOSTART_DIR/claude-mascot.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Clawd
Comment=Mascota de escritorio de Claude Code
Exec=/usr/bin/python3 $APP
Terminal=false
Categories=Utility;
EOF
  systemctl --user daemon-reload
  systemctl --user enable claude-mascot.service >/dev/null 2>&1 || true
}

start_app() {
  systemctl --user import-environment DISPLAY XAUTHORITY 2>/dev/null || true
  systemctl --user restart claude-mascot.service >/dev/null 2>&1 || true
  sleep 1
  if systemctl --user is-active claude-mascot.service >/dev/null 2>&1; then
    pause_ok "Clawd está corriendo. Clic derecho sobre ella para cerrarla."
  else
    info "No arrancó. Revisa: systemctl --user status claude-mascot"
  fi
}

do_install() {
  have_deps || install_deps || { info "Sin dependencias no puedo seguir."; return; }
  have_ollama || install_ollama
  install_files
  have_ollama && choose_model
  start_app
}

show_status() {
  local ram; ram=$(ram_gb); local ol="no"; have_ollama && ol="sí"
  local svc; svc=$(systemctl --user is-active claude-mascot.service 2>/dev/null || echo apagada)
  title "Estado"
  info "$(printf 'RAM total : %s GB\nOllama    : %s\nServicio  : %s\nApp       : %s\nModelo    : %s' \
        "$ram" "$ol" "$svc" "$([ -f "$APP" ] && echo instalada || echo 'no instalada')" "$(recommend) (recomendado)")"
}

do_uninstall() {
  confirm "¿Desinstalar Clawd? (no borra los modelos de Ollama)" || return
  systemctl --user disable --now claude-mascot.service >/dev/null 2>&1 || true
  rm -f "$UNIT" "$AUTOSTART_DIR/claude-mascot.desktop" "$APP"
  systemctl --user daemon-reload
  pause_ok "Desinstalado."
}

main() {
  while true; do
    title "Clawd · mascota de escritorio de Claude Code"
    local choice
    choice=$(menu "¿Qué quieres hacer?" \
      "Instalar (recomendado)" \
      "Elegir modelo" \
      "Comprobar dependencias" \
      "Ver estado" \
      "Desinstalar" \
      "Salir") || exit 0
    case "$choice" in
      Instalar*)  do_install ;;
      Elegir*)    choose_model ;;
      Comprobar*) have_deps && pause_ok "Dependencias OK." || install_deps ;;
      Ver*)       show_status ;;
      Desinstalar*) do_uninstall ;;
      *) exit 0 ;;
    esac
    [ "$GUM" = 1 ] && gum confirm --affirmative "Volver al menú" --negative "Salir" "" || true
    [ $? -ne 0 ] && exit 0
  done
}

main "$@"
