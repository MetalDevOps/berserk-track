# Berserk Manga Tracker

Monitora a disponibilidade de mangas Berserk na Panini Brasil e envia notificacoes push para iOS.

## Recursos

- Verificacao automatica a cada hora
- Notificacoes push para iOS (Ntfy, Pushover ou Telegram)
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

### 2. Transferir Arquivos

```bash
# No seu computador, compacte o projeto
cd berserk-track
tar -czvf berserk-tracker.tar.gz \
    berserk_tracker.py \
    requirements.txt \
    install.sh \
    uninstall.sh \
    deploy/

# Transfira para o LXC
scp berserk-tracker.tar.gz root@IP_DO_LXC:/root/
```

### 3. Instalar no LXC

```bash
# No LXC
cd /root
tar -xzvf berserk-tracker.tar.gz
cd berserk-tracker
bash install.sh
```

### 4. Configurar

```bash
# Edite a configuracao
nano /etc/berserk-tracker/config.env

# Altere o NTFY_TOPIC para algo unico:
NTFY_TOPIC=berserk-tracker-seu-nome-2024
```

### 5. Configurar Ntfy no iOS

1. Instale o app **Ntfy** da [App Store](https://apps.apple.com/app/ntfy/id1625396347)
2. Toque em `+` para adicionar inscricao
3. Digite o mesmo topico configurado (ex: `berserk-tracker-seu-nome-2024`)

### 6. Iniciar Servico

```bash
systemctl enable berserk-tracker
systemctl start berserk-tracker

# Verificar status
systemctl status berserk-tracker

# Ver logs
journalctl -u berserk-tracker -f
```

### 7. Testar Health Check

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
# Edite docker-compose.yml com seu NTFY_TOPIC
nano docker-compose.yml

# Inicie
docker-compose up -d

# Verifique
docker-compose logs -f
curl http://localhost:8080/health
```

## Comandos Uteis

```bash
# Ver logs em tempo real
journalctl -u berserk-tracker -f

# Reiniciar servico
systemctl restart berserk-tracker

# Parar servico
systemctl stop berserk-tracker

# Verificar health
curl http://localhost:8080/health

# Testar notificacao manualmente
curl -d "Teste de notificacao" ntfy.sh/seu-topico
```

## Variaveis de Ambiente

| Variavel | Padrao | Descricao |
|----------|--------|-----------|
| `CHECK_INTERVAL` | 3600 | Intervalo entre verificacoes (segundos) |
| `HEALTH_PORT` | 8080 | Porta do servidor HTTP |
| `NOTIFICATION_SERVICE` | ntfy | Servico: ntfy, pushover, telegram, none |
| `NTFY_TOPIC` | - | Seu topico unico no ntfy.sh |
| `NTFY_SERVER` | https://ntfy.sh | Servidor ntfy |
| `PUSHOVER_USER_KEY` | - | User key do Pushover |
| `PUSHOVER_API_TOKEN` | - | API token do Pushover |
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
│   ├── berserk-tracker.service  # Unit systemd
│   └── config.env.example       # Exemplo de configuracao
├── Dockerfile              # Para deploy Docker
└── docker-compose.yml      # Para deploy Docker
```

## Troubleshooting

### Servico nao inicia
```bash
journalctl -u berserk-tracker -n 50
```

### Nao recebo notificacoes
```bash
# Teste manual do ntfy
curl -d "Teste" ntfy.sh/seu-topico

# Verifique se o topico esta correto
grep NTFY_TOPIC /etc/berserk-tracker/config.env
```

### Health check retorna erro
```bash
curl -v http://localhost:8080/health
```

## Licenca

MIT
