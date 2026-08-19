FROM python:3.11-slim 
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY execution_engine.py .
CMD ["python3", "execution_engine.py"]