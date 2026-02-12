# -*- coding: utf-8 -*-
"""
Berserk Manga Availability Tracker
Verifica periodicamente a disponibilidade de mangas Berserk para compra.
Envia notificacoes push para iOS via Pushover.
Inclui servidor HTTP para health check.
"""

import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime
import logging
import json
from pathlib import Path
import os
from dataclasses import dataclass, field
from typing import Optional
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

# Configuracao de logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s", handlers=[logging.StreamHandler()])
logger = logging.getLogger(__name__)


@dataclass
class Product:
    """Representa um produto a ser monitorado."""

    name: str
    url: str


@dataclass
class HealthStatus:
    """Status da aplicacao para health check."""

    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_check: Optional[str] = None
    last_check_success: bool = True
    total_checks: int = 0
    total_errors: int = 0
    products_available: int = 0

    def to_dict(self):
        return {
            "status": "healthy" if self.last_check_success else "unhealthy",
            "started_at": self.started_at,
            "last_check": self.last_check,
            "last_check_success": self.last_check_success,
            "total_checks": self.total_checks,
            "total_errors": self.total_errors,
            "products_available": self.products_available,
            "uptime_seconds": (datetime.now() - datetime.fromisoformat(self.started_at)).total_seconds(),
        }


# Status global da aplicacao
health_status = HealthStatus()


# ============================================================================
# CONFIGURACAO - Via variaveis de ambiente
# ============================================================================

# Intervalo entre verificacoes (em segundos)
# Padrao: 3600 = 1 hora
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "3600"))

# Porta do servidor HTTP para health check
HEALTH_PORT = int(os.getenv("HEALTH_PORT", "8080"))

# Configuracao de notificacao
# Opcoes: 'pushover', 'ntfy', 'telegram', 'none'
NOTIFICATION_SERVICE = os.getenv("NOTIFICATION_SERVICE", "pushover")

# Pushover (https://pushover.net) - $5 unico, excelente para iOS
PUSHOVER_USER_KEY = os.getenv("PUSHOVER_USER_KEY", "")
PUSHOVER_API_TOKEN = os.getenv("PUSHOVER_API_TOKEN", "")

# Ntfy.sh (https://ntfy.sh) - Gratuito, open source, app iOS disponivel
NTFY_TOPIC = os.getenv("NTFY_TOPIC", "berserk-tracker-CHANGE-ME")
NTFY_SERVER = os.getenv("NTFY_SERVER", "https://ntfy.sh")

# Telegram Bot (gratuito)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")


# ============================================================================
# PRODUTOS PARA MONITORAR
# ============================================================================

PRODUCTS = [
    Product(name="Berserk Edicao de Luxo Vol. 40", url="https://panini.com.br/berserk-edicao-de-luxo-vol-40-amaxs040r"),
    Product(name="Berserk Edicao de Luxo Vol. 39", url="https://panini.com.br/berserk-edicao-de-luxo-vol-39-amaxs039r"),
    Product(name="Berserk Edicao de Luxo Vol. 37", url="https://panini.com.br/berserk-edicao-de-luxo-vol-37-amaxs037r"),
]

# Headers para simular um navegador
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    "Connection": "keep-alive",
}


# ============================================================================
# SERVIDOR HTTP PARA HEALTH CHECK
# ============================================================================


class HealthHandler(BaseHTTPRequestHandler):
    """Handler HTTP para endpoints de health check."""

    def log_message(self, format, *args):
        """Silencia logs de requisicoes HTTP."""
        pass

    def do_GET(self):
        if self.path == "/health" or self.path == "/":
            self.send_response(200 if health_status.last_check_success else 503)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            response = json.dumps(health_status.to_dict(), indent=2)
            self.wfile.write(response.encode("utf-8"))

        elif self.path == "/ready":
            # Readiness check - pronto para receber trafego
            is_ready = health_status.last_check is not None
            self.send_response(200 if is_ready else 503)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            response = json.dumps({"ready": is_ready})
            self.wfile.write(response.encode("utf-8"))

        elif self.path == "/live":
            # Liveness check - aplicacao esta viva
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            response = json.dumps({"alive": True})
            self.wfile.write(response.encode("utf-8"))

        else:
            self.send_response(404)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            response = json.dumps({"error": "Not found", "endpoints": ["/health", "/ready", "/live"]})
            self.wfile.write(response.encode("utf-8"))


def start_health_server():
    """Inicia o servidor HTTP para health check em uma thread separada."""
    server = HTTPServer(("0.0.0.0", HEALTH_PORT), HealthHandler)
    logger.info(f"Servidor de health check iniciado na porta {HEALTH_PORT}")
    server.serve_forever()


# ============================================================================
# FUNCOES DE NOTIFICACAO
# ============================================================================


def send_pushover(title: str, message: str, url: Optional[str] = None):
    """Envia notificacao via Pushover."""
    if not PUSHOVER_USER_KEY or not PUSHOVER_API_TOKEN:
        logger.warning("Pushover nao configurado. Defina PUSHOVER_USER_KEY e PUSHOVER_API_TOKEN")
        return False

    try:
        data = {
            "token": PUSHOVER_API_TOKEN,
            "user": PUSHOVER_USER_KEY,
            "title": title,
            "message": message,
            "priority": 1,
            "sound": "cashregister",
        }
        if url:
            data["url"] = url
            data["url_title"] = "Comprar Agora"

        response = requests.post("https://api.pushover.net/1/messages.json", data=data, timeout=10)
        response.raise_for_status()
        logger.info("Notificacao Pushover enviada com sucesso!")
        return True
    except Exception as e:
        logger.error(f"Erro ao enviar Pushover: {e}")
        return False


def send_ntfy(title: str, message: str, url: Optional[str] = None):
    """Envia notificacao via Ntfy.sh."""
    try:
        headers = {
            "Title": title,
            "Priority": "high",
            "Tags": "book,moneybag",
        }
        if url:
            headers["Click"] = url
            headers["Actions"] = f"view, Comprar Agora, {url}"

        response = requests.post(f"{NTFY_SERVER}/{NTFY_TOPIC}", data=message.encode("utf-8"), headers=headers, timeout=10)
        response.raise_for_status()
        logger.info("Notificacao Ntfy enviada com sucesso!")
        return True
    except Exception as e:
        logger.error(f"Erro ao enviar Ntfy: {e}")
        return False


def send_telegram(title: str, message: str, url: Optional[str] = None):
    """Envia notificacao via Telegram Bot."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("Telegram nao configurado. Defina TELEGRAM_BOT_TOKEN e TELEGRAM_CHAT_ID")
        return False

    try:
        text = f"*{title}*\n\n{message}"
        if url:
            text += f"\n\n[Comprar Agora]({url})"

        response = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": text,
                "parse_mode": "Markdown",
                "disable_web_page_preview": False,
            },
            timeout=10,
        )
        response.raise_for_status()
        logger.info("Notificacao Telegram enviada com sucesso!")
        return True
    except Exception as e:
        logger.error(f"Erro ao enviar Telegram: {e}")
        return False


def send_notification(title: str, message: str, url: Optional[str] = None):
    """Envia notificacao pelo servico configurado."""
    service = NOTIFICATION_SERVICE.lower()

    if service == "pushover":
        return send_pushover(title, message, url)
    elif service == "ntfy":
        return send_ntfy(title, message, url)
    elif service == "telegram":
        return send_telegram(title, message, url)
    elif service == "none":
        logger.info(f"Notificacao (modo none): {title} - {message}")
        return True
    else:
        logger.warning(f"Servico de notificacao desconhecido: {service}")
        return False


# ============================================================================
# FUNCOES DE VERIFICACAO
# ============================================================================


def check_panini_availability(url: str) -> tuple[bool, Optional[str]]:
    """
    Verifica disponibilidade na loja Panini.
    Retorna (disponivel, preco ou None).
    """
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()

        html_text = response.text
        soup = BeautifulSoup(html_text, "html.parser")

        # Produtos indisponiveis mostram link para 'productalert'
        if "productalert" in html_text:
            return False, None

        # Tenta encontrar o preco
        price_element = soup.find("span", {"class": "price"})
        price = price_element.get_text(strip=True) if price_element else None

        return True, price

    except requests.RequestException as e:
        logger.error(f"Erro ao acessar Panini: {e}")
        return False, None


def get_data_path() -> Path:
    """Retorna o caminho para armazenar dados persistentes."""
    # Verifica caminhos em ordem de preferencia
    for path in ["/var/lib/berserk-tracker", "/data", "."]:
        p = Path(path)
        if p.exists() and os.access(p, os.W_OK):
            return p
    return Path(".")


def load_notified_products() -> set:
    """Carrega lista de produtos ja notificados."""
    notified_file = get_data_path() / "notified_products.json"

    if notified_file.exists():
        try:
            with open(notified_file, "r") as f:
                data = json.load(f)
                return set(data.get("notified", []))
        except Exception:
            pass
    return set()


def save_notified_products(notified: set):
    """Salva lista de produtos ja notificados."""
    notified_file = get_data_path() / "notified_products.json"

    try:
        with open(notified_file, "w") as f:
            json.dump({"notified": list(notified), "updated": datetime.now().isoformat()}, f)
    except Exception as e:
        logger.error(f"Erro ao salvar produtos notificados: {e}")


def check_all_products():
    """Verifica todos os produtos e notifica se algum estiver disponivel."""
    global health_status

    logger.info("=" * 50)
    logger.info(f"Verificacao iniciada: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    logger.info("=" * 50)

    health_status.last_check = datetime.now().isoformat()
    health_status.total_checks += 1

    try:
        notified_products = load_notified_products()
        new_available = []
        available_count = 0

        for product in PRODUCTS:
            logger.info(f"Verificando: {product.name}")

            is_available, price = check_panini_availability(product.url)

            if is_available:
                available_count += 1
                price_info = f" - {price}" if price else ""
                logger.info(f"  -> DISPONIVEL!{price_info}")

                if product.url not in notified_products:
                    new_available.append({"name": product.name, "url": product.url, "price": price})
                    notified_products.add(product.url)
            else:
                logger.info("  -> Indisponivel")
                notified_products.discard(product.url)

            time.sleep(2)

        # Envia notificacoes para novos produtos disponiveis
        if new_available:
            for prod in new_available:
                price_info = f" por {prod['price']}" if prod["price"] else ""
                send_notification(
                    title="Berserk Disponivel!", message=f"{prod['name']}{price_info} esta disponivel para compra!", url=prod["url"]
                )

        save_notified_products(notified_products)

        # Atualiza status de saude
        health_status.last_check_success = True
        health_status.products_available = available_count

        logger.info(f"Proxima verificacao em {CHECK_INTERVAL} segundos ({CHECK_INTERVAL//60} min)")
        logger.info("=" * 50 + "\n")

    except Exception as e:
        logger.error(f"Erro durante verificacao: {e}")
        health_status.last_check_success = False
        health_status.total_errors += 1
        raise


def main():
    """Funcao principal."""
    global health_status

    logger.info(
        """
    ========================================================
              BERSERK MANGA TRACKER
              
       Monitorando disponibilidade dos mangas Berserk
       Notificacoes via: {service}
    ========================================================
    """.format(
            service=NOTIFICATION_SERVICE.upper()
        )
    )

    logger.info(f"Intervalo de verificacao: {CHECK_INTERVAL} segundos ({CHECK_INTERVAL//60} min)")
    logger.info(f"Produtos monitorados: {len(PRODUCTS)}")
    logger.info(f"Servico de notificacao: {NOTIFICATION_SERVICE}")
    logger.info(f"Health check: http://0.0.0.0:{HEALTH_PORT}/health")

    if NOTIFICATION_SERVICE == "ntfy":
        logger.info(f"Ntfy topic: {NTFY_TOPIC}")

    # Inicia servidor de health check em thread separada
    health_thread = threading.Thread(target=start_health_server, daemon=True)
    health_thread.start()

    # Envia notificacao de teste ao iniciar
    send_notification(
        title="Berserk Tracker Iniciado", message=f"Monitorando {len(PRODUCTS)} produtos. Intervalo: {CHECK_INTERVAL//60} min"
    )

    # Verificacao inicial
    try:
        check_all_products()
    except Exception as e:
        logger.error(f"Erro na verificacao inicial: {e}")

    # Loop principal
    while True:
        time.sleep(CHECK_INTERVAL)

        try:
            check_all_products()
        except Exception as e:
            logger.error(f"Erro durante verificacao: {e}")
            time.sleep(60)


if __name__ == "__main__":
    main()
