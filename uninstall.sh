#!/bin/bash
# Script para desinstalar o Berserk Tracker
# Execute como root: bash uninstall.sh

set -e

SERVICE_NAME="berserk-track"
LEGACY_SERVICE_NAME="berserk-tracker"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
LEGACY_SERVICE_FILE="/etc/systemd/system/${LEGACY_SERVICE_NAME}.service"

echo "=========================================="
echo "  Berserk Manga Tracker - Desinstalacao"
echo "=========================================="

# Verifica se esta rodando como root
if [ "$EUID" -ne 0 ]; then
    echo "Erro: Execute como root (sudo bash uninstall.sh)"
    exit 1
fi

echo "[1/4] Parando servico..."
systemctl stop "$SERVICE_NAME" 2>/dev/null || true
systemctl disable "$SERVICE_NAME" 2>/dev/null || true
systemctl stop "$LEGACY_SERVICE_NAME" 2>/dev/null || true
systemctl disable "$LEGACY_SERVICE_NAME" 2>/dev/null || true

APP_DIR=$(systemctl cat "$SERVICE_NAME" 2>/dev/null | sed -n 's/^WorkingDirectory=//p' | tail -n 1)
if [ -z "$APP_DIR" ]; then
    APP_DIR=$(systemctl cat "$LEGACY_SERVICE_NAME" 2>/dev/null | sed -n 's/^WorkingDirectory=//p' | tail -n 1)
fi
if [ -z "$APP_DIR" ]; then
    APP_DIR="/opt/berserk-track"
fi

echo "[2/4] Removendo arquivos do systemd..."
rm -f "$SERVICE_FILE"
rm -f "$LEGACY_SERVICE_FILE"
systemctl daemon-reload

echo "[3/4] Removendo arquivos da aplicacao..."
rm -rf "$APP_DIR"

echo "[4/4] Removendo usuario..."
userdel berserk-tracker 2>/dev/null || true

echo ""
echo "=========================================="
echo "  Desinstalacao concluida!"
echo "=========================================="
echo ""
echo "Os seguintes arquivos foram mantidos:"
echo "  - /etc/berserk-tracker/config.env (configuracao)"
echo "  - /var/lib/berserk-tracker/ (dados)"
echo ""
echo "Para remover completamente:"
echo "  rm -rf /etc/berserk-tracker /var/lib/berserk-tracker"
echo ""
