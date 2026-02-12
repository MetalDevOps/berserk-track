# Berserk Manga Tracker

Monitora a disponibilidade de mangas Berserk na Panini Brasil e envia notificacoes push para iOS.

## Recursos

- Verificacao automatica a cada hora
- Notificacoes push para iOS (Pushover, Ntfy ou Telegram)
- Endpoint `/health` para monitoramento
- Deploy simples em LXC ou Docker
- Evita notificacoes duplicadas

## Deploy no Proxmox LXC (Recomendado)

### 1. Criar Container LXC

No Proxmox, crie um container:
- **Template**: Debian 12 ou Ubuntu 22.04
- **RAM**: 256MB
- **Disco**: 2GB
- **CPU**: 1 core

### 2. Instalar no LXC

```bash
# Instalar git
apt update && apt install -y git

# Clonar repositorio
cd /opt
git clone https://github.com/MetalDevOps/berserk-track.git
cd berserk-track

# Executar instalacao
bash install.sh
```

### 3. Configurar

```bash
# Edite a configuracao
nano /etc/berserk-tracker/config.env

# Configure suas credenciais do Pushover:
NOTIFICATION_SERVICE=pushover
PUSHOVER_USER_KEY=seu_user_key
PUSHOVER_API_TOKEN=seu_api_token
```

### 4. Configurar Pushover no iOS

1. Instale o app **Pushover** da [App Store](https://apps.apple.com/us/app/pushover-notifications/id506088175)
2. Crie sua conta e copie o **User Key**
3. Em [pushover.net/apps/build](https://pushover.net/apps/build), crie um app e copie o **API Token**
4. Preencha `PUSHOVER_USER_KEY` e `PUSHOVER_API_TOKEN` no `config.env`

### 5. Iniciar Servico

```bash
systemctl enable berserk-track
systemctl start berserk-track

# Verificar status
systemctl status berserk-track

# Ver logs
journalctl -u berserk-track -f
```

### 6. Testar Health Check

```bash
curl http://localhost:8080/health
```

Resposta esperada:
```json
{
  "status": "healthy",
  "last_check": "2024-01-15T10:00:00",
  "total_checks": 5,
  "products_available": 0
}
```

## Endpoints HTTP

| Endpoint | Descricao |
|----------|-----------|
| `/health` | Status completo da aplicacao |
| `/ready` | Readiness check (pronto para uso) |
| `/live` | Liveness check (aplicacao viva) |

## Deploy com Docker (Alternativo)

Se preferir usar Docker:

```bash
# Clonar repositorio
git clone https://github.com/MetalDevOps/berserk-track.git
cd berserk-track

# Edite docker-compose.yml com suas credenciais PUSHOVER
nano docker-compose.yml

# Inicie
docker-compose up -d

# Verifique
docker-compose logs -f
curl http://localhost:8080/health
```

## Atualizar

Para atualizar para a versao mais recente:

```bash
cd /opt/berserk-track
bash install.sh
```

O `install.sh` funciona como **install/update**: faz `git pull` (quando possivel), atualiza o venv e reinicia o servico.

## Comandos Uteis

```bash
# Ver logs em tempo real
journalctl -u berserk-track -f

# Reiniciar servico
systemctl restart berserk-track

# Parar servico
systemctl stop berserk-track

# Verificar health
curl http://localhost:8080/health

# Testar notificacao manualmente via Pushover
curl -s \
  -F "token=SEU_API_TOKEN" \
  -F "user=SEU_USER_KEY" \
  -F "title=Berserk Tracker" \
  -F "message=Teste de notificacao" \
  https://api.pushover.net/1/messages.json
```

## Variaveis de Ambiente

| Variavel | Padrao | Descricao |
|----------|--------|-----------|
| `CHECK_INTERVAL` | 3600 | Intervalo entre verificacoes (segundos) |
| `HEALTH_PORT` | 8080 | Porta do servidor HTTP |
| `NOTIFICATION_SERVICE` | pushover | Servico: pushover, ntfy, telegram, none |
| `PUSHOVER_USER_KEY` | - | User key do Pushover |
| `PUSHOVER_API_TOKEN` | - | API token do Pushover |
| `NTFY_TOPIC` | - | Seu topico unico no ntfy.sh (se usar ntfy) |
| `NTFY_SERVER` | https://ntfy.sh | Servidor ntfy (se usar ntfy) |
| `TELEGRAM_BOT_TOKEN` | - | Token do bot Telegram |
| `TELEGRAM_CHAT_ID` | - | Chat ID do Telegram |

## Produtos Monitorados

- Berserk Edicao de Luxo Vol. 40
- Berserk Edicao de Luxo Vol. 39
- Berserk Edicao de Luxo Vol. 37

Para adicionar/remover produtos, edite a lista `PRODUCTS` em `berserk_tracker.py`.

## Estrutura de Arquivos

```
berserk-track/
├── berserk_tracker.py      # Script principal
├── requirements.txt        # Dependencias Python
├── install.sh              # Script de instalacao LXC
├── uninstall.sh            # Script de desinstalacao
├── deploy/
│   ├── berserk-track.service  # Unit systemd
│   └── config.env.example       # Exemplo de configuracao
├── Dockerfile              # Para deploy Docker
└── docker-compose.yml      # Para deploy Docker
```

## Troubleshooting

### Servico nao inicia
```bash
journalctl -u berserk-track -n 50
```

### Nao recebo notificacoes
```bash
# Verifique as credenciais do Pushover
grep -E "NOTIFICATION_SERVICE|PUSHOVER_USER_KEY|PUSHOVER_API_TOKEN" /etc/berserk-tracker/config.env

# Teste manual do Pushover
curl -s \
  -F "token=SEU_API_TOKEN" \
  -F "user=SEU_USER_KEY" \
  -F "title=Berserk Tracker" \
  -F "message=Teste" \
  https://api.pushover.net/1/messages.json
```

### Health check retorna erro
```bash
curl -v http://localhost:8080/health
```

## Licenca

MIT
