FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip \
    && python -m pip install --no-cache-dir -r /app/requirements.txt
RUN pip install -U sentence-transformers

RUN useradd --create-home --uid 10001 appuser
USER appuser

COPY --chown=appuser:appuser . /app

HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD python -c "import config.settings; print('ok')" || exit 1

CMD ["python", "main.py", "chat"]
