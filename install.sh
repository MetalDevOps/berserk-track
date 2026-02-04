#!/bin/bash
# Script de instalacao do Berserk Tracker no LXC
# Execute como root: bash install.sh
# 
# Uso:
#   git clone https://github.com/MetalDevOps/berserk-track.git
#   cd berserk-track
#   bash install.sh

set -e

REPO_URL="https://github.com/MetalDevOps/berserk-track.git"
INSTALL_DIR="/opt/berserk-tracker"

echo "=========================================="
echo "  Berserk Manga Tracker - Instalacao"
echo "=========================================="

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Verifica se esta rodando como root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Erro: Execute como root (sudo bash install.sh)${NC}"
    exit 1
fi

# Detecta diretorio atual (onde o script foi executado)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${GREEN}[1/7]${NC} Atualizando sistema..."
apt update && apt upgrade -y

echo -e "${GREEN}[2/7]${NC} Instalando dependencias..."
apt install -y python3 python3-venv python3-pip curl git

echo -e "${GREEN}[3/7]${NC} Criando usuario do servico..."
if ! id "berserk-tracker" &>/dev/null; then
    useradd --system --no-create-home --shell /bin/false berserk-tracker
fi

echo -e "${GREEN}[4/7]${NC} Criando diretorios..."
mkdir -p /etc/berserk-tracker
mkdir -p /var/lib/berserk-tracker

echo -e "${GREEN}[5/7]${NC} Copiando arquivos..."
# Se executado de dentro do repo clonado, copia os arquivos
if [ -f "$SCRIPT_DIR/berserk_tracker.py" ]; then
    mkdir -p $INSTALL_DIR
    cp "$SCRIPT_DIR/berserk_tracker.py" $INSTALL_DIR/
    cp "$SCRIPT_DIR/requirements.txt" $INSTALL_DIR/
    
    if [ ! -f /etc/berserk-tracker/config.env ]; then
        cp "$SCRIPT_DIR/deploy/config.env.example" /etc/berserk-tracker/config.env
        echo -e "${YELLOW}IMPORTANTE: Edite /etc/berserk-tracker/config.env com suas configuracoes${NC}"
    fi
    
    cp "$SCRIPT_DIR/deploy/berserk-tracker.service" /etc/systemd/system/
else
    echo -e "${YELLOW}Clonando repositorio...${NC}"
    git clone $REPO_URL $INSTALL_DIR
    
    if [ ! -f /etc/berserk-tracker/config.env ]; then
        cp "$INSTALL_DIR/deploy/config.env.example" /etc/berserk-tracker/config.env
        echo -e "${YELLOW}IMPORTANTE: Edite /etc/berserk-tracker/config.env com suas configuracoes${NC}"
    fi
    
    cp "$INSTALL_DIR/deploy/berserk-tracker.service" /etc/systemd/system/
fi
cp deploy/berserk-tracker.service /etc/systemd/system/

echo -e "${GREEN}[6/7]${NC} Criando ambiente virtual Python..."
cd /opt/berserk-tracker
python3 -m venv venv
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt

echo -e "${GREEN}[7/7]${NC} Configurando permissoes..."
chown -R berserk-tracker:berserk-tracker /opt/berserk-tracker
chown -R berserk-tracker:berserk-tracker /var/lib/berserk-tracker
chmod 600 /etc/berserk-tracker/config.env

echo -e "${GREEN}[OK]${NC} Recarregando systemd..."
systemctl daemon-reload

echo ""
echo "=========================================="
echo -e "${GREEN}  Instalacao concluida!${NC}"
echo "=========================================="
echo ""
echo "Proximos passos:"
echo ""
echo "1. Edite a configuracao:"
echo "   nano /etc/berserk-tracker/config.env"
echo ""
echo "2. Altere NTFY_TOPIC para um valor unico:"
echo "   Ex: berserk-tracker-$(hostname)-$(date +%s)"
echo ""
echo "3. Inicie o servico:"
echo "   systemctl enable berserk-tracker"
echo "   systemctl start berserk-tracker"
echo ""
echo "4. Verifique o status:"
echo "   systemctl status berserk-tracker"
echo "   journalctl -u berserk-tracker -f"
echo ""
echo "5. Teste o health check:"
echo "   curl http://localhost:8080/health"
echo ""
