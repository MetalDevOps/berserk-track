#!/bin/bash
# Script de instalacao do Berserk Tracker no LXC
# Execute como root: bash install.sh
# 
# Uso:
#   git clone https://github.com/MetalDevOps/berserk-track.git
#   cd berserk-track
#   bash install.sh

set -e

echo "=========================================="
echo "  Berserk Manga Tracker - Install/Update"
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
SCRIPT_DIR_REAL="$(cd "$SCRIPT_DIR" && pwd -P)"
SERVICE_FILE="/etc/systemd/system/berserk-tracker.service"
CONFIG_DIR="/etc/berserk-tracker"
CONFIG_FILE="$CONFIG_DIR/config.env"
DATA_DIR="/var/lib/berserk-tracker"
LEGACY_DIR="/opt/berserk-tracker"

detect_previous_installation() {
    PREV_APP_DIR=""

    if systemctl cat berserk-tracker >/dev/null 2>&1; then
        PREV_APP_DIR=$(systemctl cat berserk-tracker | sed -n 's/^WorkingDirectory=//p' | tail -n 1)
    elif [ -f "$SERVICE_FILE" ]; then
        PREV_APP_DIR=$(sed -n 's/^WorkingDirectory=//p' "$SERVICE_FILE" | tail -n 1)
    fi

    NEED_UNINSTALL=0
    if [ -n "$PREV_APP_DIR" ] && [ "$PREV_APP_DIR" != "$SCRIPT_DIR_REAL" ]; then
        NEED_UNINSTALL=1
    fi

    if [ -d "$LEGACY_DIR" ] && [ "$LEGACY_DIR" != "$SCRIPT_DIR_REAL" ]; then
        NEED_UNINSTALL=1
    fi
}

uninstall_previous_installation() {
    echo -e "${YELLOW}[INFO]${NC} Instalacao anterior detectada. Executando uninstall..."

    systemctl stop berserk-tracker 2>/dev/null || true
    systemctl disable berserk-tracker 2>/dev/null || true
    rm -f "$SERVICE_FILE"
    systemctl daemon-reload

    if [ -n "$PREV_APP_DIR" ] && [ -d "$PREV_APP_DIR" ] && [ "$PREV_APP_DIR" != "$SCRIPT_DIR_REAL" ]; then
        rm -rf "$PREV_APP_DIR"
    fi

    if [ -d "$LEGACY_DIR" ] && [ "$LEGACY_DIR" != "$SCRIPT_DIR_REAL" ]; then
        rm -rf "$LEGACY_DIR"
    fi
}

echo -e "${GREEN}[1/9]${NC} Atualizando pacotes do sistema..."
apt update

echo -e "${GREEN}[2/9]${NC} Instalando dependencias..."
apt install -y python3 python3-venv python3-pip curl git

echo -e "${GREEN}[3/9]${NC} Validando repositorio local..."
if [ ! -f "$SCRIPT_DIR/berserk_tracker.py" ] || [ ! -f "$SCRIPT_DIR/requirements.txt" ]; then
    echo -e "${RED}Erro: execute este script dentro do repositorio berserk-track clonado.${NC}"
    exit 1
fi

echo -e "${GREEN}[4/9]${NC} Verificando instalacao anterior..."
detect_previous_installation
if [ "$NEED_UNINSTALL" -eq 1 ]; then
    uninstall_previous_installation
else
    echo -e "${GREEN}[INFO]${NC} Nenhuma instalacao anterior conflitante encontrada."
fi

if git -C "$SCRIPT_DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo -e "${GREEN}[INFO]${NC} Atualizando codigo com git pull..."
    if ! git -C "$SCRIPT_DIR" pull --ff-only; then
        echo -e "${YELLOW}Aviso:${NC} nao foi possivel executar git pull --ff-only (possiveis mudancas locais). Seguindo com os arquivos atuais."
    fi
else
    echo -e "${YELLOW}Aviso:${NC} diretorio atual nao parece ser um repositorio git. Seguindo sem git pull."
fi

echo -e "${GREEN}[5/9]${NC} Criando usuario do servico..."
if ! id "berserk-tracker" &>/dev/null; then
    useradd --system --no-create-home --shell /bin/false berserk-tracker
fi

echo -e "${GREEN}[6/9]${NC} Criando diretorios e configuracao..."
mkdir -p "$CONFIG_DIR"
mkdir -p "$DATA_DIR"
if [ ! -f "$CONFIG_FILE" ]; then
    cp "$SCRIPT_DIR/deploy/config.env.example" "$CONFIG_FILE"
    echo -e "${YELLOW}IMPORTANTE: Edite $CONFIG_FILE com suas configuracoes${NC}"
fi

echo -e "${GREEN}[7/9]${NC} Instalando dependencias Python no venv..."
cd "$SCRIPT_DIR"
python3 -m venv venv
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt

echo -e "${GREEN}[8/9]${NC} Gerando unit file do systemd..."
cat > "$SERVICE_FILE" <<EOF
[Unit]
Description=Berserk Manga Availability Tracker
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=berserk-tracker
Group=berserk-tracker
WorkingDirectory=$SCRIPT_DIR
ExecStart=$SCRIPT_DIR/venv/bin/python $SCRIPT_DIR/berserk_tracker.py
Restart=always
RestartSec=30
EnvironmentFile=$CONFIG_FILE
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$DATA_DIR
PrivateTmp=true
StandardOutput=journal
StandardError=journal
SyslogIdentifier=berserk-tracker

[Install]
WantedBy=multi-user.target
EOF

echo -e "${GREEN}[9/9]${NC} Ajustando permissoes e reiniciando servico..."
chown -R berserk-tracker:berserk-tracker "$SCRIPT_DIR"
chown -R berserk-tracker:berserk-tracker "$DATA_DIR"
chmod 600 "$CONFIG_FILE"

systemctl daemon-reload
systemctl enable berserk-tracker
if systemctl is-active --quiet berserk-tracker; then
    systemctl restart berserk-tracker
else
    systemctl start berserk-tracker
fi

echo ""
echo "=========================================="
echo -e "${GREEN}  Install/Update concluido!${NC}"
echo "=========================================="
echo ""
echo "Proximos passos:"
echo ""
echo "1. Edite a configuracao:"
echo "   nano /etc/berserk-tracker/config.env"
echo ""
echo "2. Configure o Pushover no config.env:"
echo "   NOTIFICATION_SERVICE=pushover"
echo "   PUSHOVER_USER_KEY=seu_user_key"
echo "   PUSHOVER_API_TOKEN=seu_api_token"
echo ""
echo "3. O servico ja foi iniciado/reiniciado automaticamente."
echo ""
echo "4. Verifique o status:"
echo "   systemctl status berserk-tracker"
echo "   journalctl -u berserk-tracker -f"
echo ""
echo "5. Teste o health check:"
echo "   curl http://localhost:8080/health"
echo ""
