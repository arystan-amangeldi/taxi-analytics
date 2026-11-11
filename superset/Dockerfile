FROM apache/superset:6.1.0

USER root

RUN uv pip install --python /app/.venv/bin/python \
    "clickhouse-connect==1.11.0"

COPY --chown=superset:superset \
    superset_config.py /app/superset_config.py

ENV SUPERSET_CONFIG_PATH=/app/superset_config.py

USER superset