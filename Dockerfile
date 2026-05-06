FROM python:3.11-slim

WORKDIR /app

ARG APT_MIRROR=http://mirrors.cloud.tencent.com/debian
ARG APT_SECURITY_MIRROR=http://mirrors.cloud.tencent.com/debian-security

RUN printf 'Acquire::Retries "5";\nAcquire::http::Timeout "60";\nAcquire::https::Timeout "60";\n' > /etc/apt/apt.conf.d/99-retries && \
    if [ -f /etc/apt/sources.list.d/debian.sources ]; then \
        sed -i \
            -e "s|http://deb.debian.org/debian|${APT_MIRROR}|g" \
            -e "s|https://deb.debian.org/debian|${APT_MIRROR}|g" \
            -e "s|http://deb.debian.org/debian-security|${APT_SECURITY_MIRROR}|g" \
            -e "s|https://deb.debian.org/debian-security|${APT_SECURITY_MIRROR}|g" \
            /etc/apt/sources.list.d/debian.sources; \
    else \
        sed -i \
            -e "s|http://deb.debian.org/debian|${APT_MIRROR}|g" \
            -e "s|https://deb.debian.org/debian|${APT_MIRROR}|g" \
            -e "s|http://deb.debian.org/debian-security|${APT_SECURITY_MIRROR}|g" \
            -e "s|https://deb.debian.org/debian-security|${APT_SECURITY_MIRROR}|g" \
            /etc/apt/sources.list; \
    fi && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        libreoffice \
        fonts-noto-cjk \
        fonts-wqy-zenhei && \
    rm -rf /var/lib/apt/lists/*

RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/ && \
    pip config set global.trusted-host mirrors.aliyun.com

RUN useradd -m -u 1000 appuser

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=appuser:appuser app/ ./app/

RUN mkdir -p /app/data/files && chown -R appuser:appuser /app

ENV PYTHONPATH=/app
ENV APP_ENV=production
ENV MCP_TRANSPORT=streamable-http
ENV MCP_HOST=0.0.0.0
ENV MCP_PORT=8010

USER appuser

EXPOSE 8000 8010

CMD ["python", "-m", "app.mcp_server.server"]
