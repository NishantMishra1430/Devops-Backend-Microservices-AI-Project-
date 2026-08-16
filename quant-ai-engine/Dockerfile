
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt ./
RUN apt-get update -y && apt-get upgrade -y && pip install --no-cache-dir -r requirements.txt
COPY . . 
USER nobody
EXPOSE 3002
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3002"]