FROM python:3.11-slim 
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
RUN useradd -m authuser
WORKDIR /app
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl libpq-dev gcc build-essential && \
    rm -rf /var/lib/apt/lists/*
COPY --chown=authuser:authuser requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt 
RUN apt-get purge -y --auto-remove gcc build-essential
COPY --chown=authuser:authuser app/ ./app/
USER authuser 
EXPOSE 3006
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "3006"]
