FROM python:3.11-slim 
WORKDIR /app
COPY requirements.txt ./
RUN apt-get update && \
    apt-get install -y --only-upgrade perl-base && \
    rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir -r requirements.txt
COPY execution_engine.py .
CMD ["python3", "execution_engine.py"]