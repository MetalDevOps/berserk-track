FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar script
COPY berserk_tracker.py .

# Criar diretorio para dados persistentes
RUN mkdir -p /data

# Executar como usuario nao-root
RUN useradd -m -u 1000 tracker
RUN chown -R tracker:tracker /app /data
USER tracker

# Variaveis de ambiente padrao
ENV CHECK_INTERVAL=3600
ENV HEALTH_PORT=8080
ENV NOTIFICATION_SERVICE=ntfy
ENV NTFY_TOPIC=berserk-tracker-CHANGE-ME
ENV NTFY_SERVER=https://ntfy.sh
ENV PYTHONUNBUFFERED=1

# Expor porta do health check
EXPOSE 8080

# Health check usando o endpoint HTTP
HEALTHCHECK --interval=5m --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

CMD ["python", "berserk_tracker.py"]
