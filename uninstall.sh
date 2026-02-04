#!/bin/bash
# Script para desinstalar o Berserk Tracker
# Execute como root: bash uninstall.sh

set -e

echo "=========================================="
echo "  Berserk Manga Tracker - Desinstalacao"
echo "=========================================="

# Verifica se esta rodando como root
if [ "$EUID" -ne 0 ]; then
    echo "Erro: Execute como root (sudo bash uninstall.sh)"
    exit 1
fi

echo "[1/4] Parando servico..."
systemctl stop berserk-tracker 2>/dev/null || true
systemctl disable berserk-tracker 2>/dev/null || true

echo "[2/4] Removendo arquivos do systemd..."
rm -f /etc/systemd/system/berserk-tracker.service
systemctl daemon-reload

echo "[3/4] Removendo arquivos da aplicacao..."
rm -rf /opt/berserk-tracker

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
