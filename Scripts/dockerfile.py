# Create a function which create a Dockerfile inside every folder and then insert file content in it.
# make a function which run Docker containers 
from pathlib import Path 

main = Path(".")
folders = ["api-gateway", "notification-service", "execution-service", "market-data-service", "quant-ai-engine"]

node_dockerfile = """
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install --omit=dev
COPY . .
USER node
CMD ["npm", "start"]
"""
python_dockerfile = """
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt ./
RUN apt-get update -y &&\
apt-get upgrade -y &&\
pip install --no-cache-dir -r requirements.txt
COPY . . 
USER nobody
EXPOSE 3002
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3002"]"""
dockerignore = """
.env
.env.example
logs/
.git
*.md
cache"""

def dockerfile():
    
    for folder in folders:
        docker = main / folder / "Dockerfile"
        dockerig = main / folder / ".dockerignore"
        if not dockerig.exists():
            print(f"Creating {dockerig} file in {folder} folder")
            dockerig.touch()
            dockerig.write_text(dockerignore)
        else:
            print(f"{dockerig} file is already exists")
            dockerig.write_text(dockerignore)
        if not docker.exists():
            docker.touch()
            if not folder == "quant-ai-engine":
                docker.write_text(node_dockerfile)
            else:
                docker.write_text(python_dockerfile)
        else:
            print(f"{docker} is already Exists")

dockerfile()