# Algorithmic Quantitative Trading Platform

## 📌 Overview
This repository contains the source code for a high-performance, event-driven quantitative trading platform. The system is designed to ingest real-time market data, evaluate complex algorithmic and machine-learning models, and execute trades with minimal latency. 

Built on a highly decoupled microservices architecture, the platform separates concerns across data ingestion, strategy evaluation, risk management, and order execution, ensuring high availability and scalability for intensive computational workloads.

---

## 🧠 System Architecture & Data Flow
The application operates on an asynchronous, event-driven model to ensure real-time responsiveness. 

1. **Market Data Ingestion:** Live market data is continuously streamed into the system via WebSockets and REST APIs.
2. **Signal Generation:** The AI/Quant engine processes the incoming data streams against pre-trained models to identify trading opportunities and generates buy/sell signals.
3. **Event Routing:** Signals are published to a message broker (RabbitMQ), decoupling the heavy computation from the execution logic.
4. **Order Execution:** Consumers pick up the signals, validate risk and account balances, and route the finalized orders to external exchange APIs.
5. **Client Updates:** The execution results are saved to the database and pushed back to the client UI in real-time via the API Gateway's WebSocket connections.

---

## 🏗️ Microservices Directory
The platform is composed of specialized microservices, each handling a distinct domain of the trading lifecycle.

### 1. Edge & User Interface
*   **`api-gateway` (Node.js):** The central entry point for all client traffic. Manages long-lived WebSocket connections for real-time dashboard updates and routes standard HTTP requests to internal services.
*   **`frontend-service`:** The user-facing web application that provides real-time portfolio tracking, charting, and manual trade management capabilities.

### 2. Identity & Security
*   **`auth-service` (Python):** Handles user authentication, session management, and JWT (JSON Web Token) issuance. Secures internal API routes and validates user permissions.

### 3. Core Quantitative Logic (The Brains)
*   **`market-data-service`:** Connects to external exchanges (e.g., Binance, NSE) to stream live order book data, tick data, and historical OHLCV candles. 
*   **`quant-ai-engine` (Python):** The computational core of the platform. Houses the machine learning models (PyTorch/Scikit-learn), statistical arbitrage logic, and algorithmic strategies that analyze market data to generate trading signals.

### 4. Trade Execution (The Brawn)
*   **`execution-engine` (Python):** The risk management and routing layer. It intercepts trade signals, verifies user balances, checks risk limits, and formats the final order.
*   **`execution-service`:** The outbound communication layer that interfaces directly with external broker/exchange APIs to place, modify, or cancel actual market/limit orders.

### 5. Event Streaming & Asynchronous Processing
*   **`rabbitmq`:** The central message broker enabling decoupled, asynchronous communication between microservices.
*   **`producer`:** A utility service/module responsible for standardizing and publishing internal events (e.g., `SignalGenerated`, `OrderPlaced`) to RabbitMQ exchanges.
*   **`consumer` (Python):** Background workers that listen to RabbitMQ queues and trigger downstream logic without blocking the main application threads.
*   **`notification-service`:** Listens for critical system events or completed trades and dispatches real-time alerts via Email, Slack, or Discord.

### 6. State & Persistence
*   **`postgres`:** The primary relational database for persistent storage. Holds user profiles, wallet balances, strict transactional records, and historical trade logs.
*   **`redis`:** A high-speed, in-memory data store used for caching API responses, maintaining real-time order books, managing rate limits, and storing temporary session states.

---

## 🛠️ Technology Stack
*   **Backend Runtimes:** Python 3.11 (Data Science & Execution), Node.js (API Gateway)
*   **Communication:** REST APIs, WebSockets (Real-time data), AMQP (RabbitMQ)
*   **Data Layer:** PostgreSQL, Redis
*   **Machine Learning:** Python Data Science Ecosystem (Pandas, NumPy, Scikit-learn)


## 🐳 Local Development with Docker Compose

This section details how to quickly spin up a local development environment using Docker Compose. This allows you to run the entire quantitative trading platform (databases, message brokers, and all microservices) locally with a single command, without needing a full Kubernetes cluster.

### Prerequisites
* [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running.
* Docker Compose installed (usually included with Docker Desktop).

### Environment Variables
For local development and testing, all required environment variables (like database credentials and API URLs) are already pre-configured and hardcoded directly inside the `compose.yaml` file. **You do not need to create a `.env` file to run this stack locally.**

### Architecture Overview (Local)
The `compose.yaml` file sets up a dedicated Docker network (`quant_net`) and provisions the following components:

**1. Infrastructure & State (Data Layer)**
* **Postgres (`5432`):** Relational database mapped to a persistent local volume (`pg_data`).
* **Redis (`6379`):** In-memory cache for market data and real-time state.
* **RabbitMQ (`5672` / `15672`):** Message broker for async communication. The management UI is exposed on port `15672`.

**2. Microservices (Application Layer)**
* **Frontend UI:** `http://localhost:8080`
* **API Gateway:** `http://localhost:3000`
* **Core Services:** `auth-service`, `market-data-service`, `quant-ai-engine`, `execution-service`, `notification-service`, `producer`, `consumer`, and `execution-engine`.

*Note: The microservices are built directly from their respective local directories using their individual `Dockerfile`s.*

---

### 🚀 Running the Platform

**1. Start the entire stack**
Navigate to the root directory of the project (where `compose.yaml` is located) and run:
```bash
docker compose up --build -d
```
--build: Forces Docker to build the fresh images from your local source code directories.

-d: Runs the containers in detached mode (in the background).

**2. Verify the services are running**
Wait a few moments for the infrastructure (Postgres, Redis, RabbitMQ) to pass their health checks and for the dependent microservices to spin up. Check the status of all containers:

```bash
docker compose ps
```

**3. Accessing the Application locally**
Once everything is running, you can access the local environment via your browser or API testing tools:

Frontend Web App: http://localhost:8080

API Gateway (Backend Entrypoint): http://localhost:3000

RabbitMQ Management Dashboard: http://localhost:15672 (Default login is usually guest / guest).

### 🛠️ Useful Commands for Debugging

**View logs for a specific service (e.g., the AI engine):**
```bash
docker compose logs -f quant-ai-engine
```

**Restart a single service after making code changes:**
```bash
docker compose up -d --build execution-service
```

**Stop the environment without losing database state:**
```bash
docker compose down
```

**Stop the environment AND wipe all local database/cache data (Clean Slate):**
```bash
docker compose down -v
```

# Kubernetes Configuration & Secrets Management

## 📌 Overview
This guide provides the imperative setup commands to bootstrap all **Secrets** and **ConfigMaps** required by the microservices in the `quant` namespace. 

*   **Secrets (`Opaque`):** Used to isolate sensitive connection strings, database credentials, and cryptographic tokens from version control.
*   **ConfigMaps:** Used to store non-sensitive service discovery endpoints, internal DNS records, and server reverse-proxy configurations (`nginx.conf`).

---

## 🔐 1. Secrets Provisioning

Ensure the target namespace exists before provisioning secrets:
```bash
kubectl create namespace quant --dry-run=client -o yaml | kubectl apply -f -
```
## A. Database Credentials (quant-postgres)

Stores the administrative username and password for the PostgreSQL stateful deployment.

```bash
kubectl create secret generic quant-postgres \
  --namespace=quant \
  --from-literal=puser="" \
  --from-literal=ppassword=""
```

## B. Identity & Cryptography (jwt-secrets)

Holds the signing key used by auth-service to sign and verify JSON Web Tokens (JWT).
```bash
kubectl create secret generic jwt-secrets \
  --namespace=quant \
  --from-literal=jwt_secret_key="" 
```

## C. Infrastructure Connection Strings (data-url)

Contains the internal connection URIs for Redis, RabbitMQ, and PostgreSQL used across the microservices.
```bash
kubectl create secret generic data-url \
  --namespace=quant \
  --from-literal=redis-url="redis://redis:6379" \
  --from-literal=rabbitmq-url="amqp://rabbitmq:5672" \
  --from-literal=db-url="postgres://postgres:password@postgres:5432/quanttrade" \
  --from-literal=database-url="postgresql+asyncpg://postgres:password@postgres:5432/quanttrade"
```

## ⚙️ 2. ConfigMaps Provisioning
### A. Internal Service Discovery (service-url)

Maps microservice names to their internal Kubernetes DNS and exposed public NodePort endpoints.

```bash
kubectl create configmap service-url \
  --namespace=quant \
  --from-literal=auth-service="http://auth:3006" \
  --from-literal=execution-service="http://quant-execution:3003" \
  --from-literal=market-data="http://market-data-service:3001" \
  --from-literal=quant-engine="http://ai-engine:3002" \
  --from-literal=vite-api-url="[http://157.173.121.36:30080](http://157.173.121.36:30080)" \
  --from-literal=vite-ws-url="ws://157.173.121.36:30080/ws/"
```

### B. Frontend Reverse Proxy Configuration (frontend-nginx-config)

Mounts the Nginx reverse-proxy rules and WebSocket upgrade headers directly into the frontend-service container.

**1. Create the default.conf file locally:**
```bash
cat <<'EOF' > default.conf
server {
    listen 80;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri$uri/ /index.html;
    }

    location /auth/ {
        proxy_pass http://auth:3006/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /market/ {
        proxy_pass http://api-gateway:3000/market/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /quant/ {
        proxy_pass http://api-gateway:3000/quant/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /trade/ {
        proxy_pass http://api-gateway:3000/trade/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /ws/ {
        proxy_pass http://api-gateway:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400;
    }

    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
    gzip_min_length 1000;
}
EOF
```
**2. Create the ConfigMap from the local file:**
```bash
kubectl create configmap frontend-nginx-config \
  --namespace=quant \
  --from-file=default.conf=./default.conf
```
## 🔍 3. Verification Commands

Run the following commands to confirm that all required resources are loaded:
```bash
# Verify all secrets exist
kubectl get secrets -n quant

# Verify all configmaps exist
kubectl get configmaps -n quant

# Inspect specific secret keys
kubectl describe secret data-url -n quant

# Inspect the loaded Nginx configuration
kubectl get configmap frontend-nginx-config -n quant -o yaml
```

## 🔄 4. How Pods Consume These Resources

**Environment Variables via Secret/ConfigMap Key:**
```bash
env:
  - name: REDIS_URL
    valueFrom:
      secretKeyRef:
        name: data-url
        key: redis-url
```

**Volume Mount for Nginx ConfigMap:**
```bash
volumeMounts:
  - name: nginx-config
    mountPath: /etc/nginx/conf.d/default.conf
    subPath: default.conf
volumes:
  - name: nginx-config
    configMap:
      name: frontend-nginx-config
```

## ☸️ Production Deployment (GitOps, Helm & ArgoCD)

While Docker Compose is used for local development, the production environment is deployed and managed using a strict **GitOps** methodology on Kubernetes.

To ensure a clean separation of concerns between application source code and infrastructure state, all deployment configurations have been moved to a dedicated **GitOps Configuration Repository**.

### 🧠 The GitOps Architecture
Our deployment pipeline utilizes the following cloud-native technologies:

*   **GitOps:** A modern continuous delivery model where a Git repository acts as the single source of truth for the target environment. No manual `kubectl` commands are used in production.
*   **Helm:** All microservices (API Gateway, AI Engine, Auth, etc.) are packaged into reusable **Helm Charts**. This allows us to dynamically inject environment-specific values and manage complex Kubernetes YAMLs efficiently.
*   **ArgoCD:** The declarative GitOps controller running inside our Kubernetes cluster. ArgoCD continuously monitors the Config-Repo. If it detects a change (e.g., a new image tag pushed by CI), it automatically reconciles and syncs the live cluster to match the desired state in Git.

### 🔗 Explore the Infrastructure
To view the Kubernetes manifests, Helm charts, Observability stack (Prometheus/Loki), and ArgoCD application definitions, please visit the Config-Repo:

👉 **[View the GitOps Configuration Repository Here](https://github.com/NishantMishra1430/Config-Repo-of-DevOps-Backend-Microservices-Application-.git)**

## ⚙️ Continuous Integration (CI) & Pipeline Architecture

To bridge the gap between our source code and the GitOps CD pipeline, we utilize GitHub Actions. The CI architecture is designed to handle multiple microservices building simultaneously while enforcing strict security scans and preventing Git push race conditions.

### 🔄 High-Level CI/CD & Concurrency Orchestration

When a developer pushes code, multiple microservice pipelines may trigger in parallel. To prevent race conditions when multiple jobs attempt to update the shared `values.yaml` in the Config-Repo simultaneously, the final update step is routed through a serialized concurrency queue.

<p align="center">
  <img src="./diagram/Screenshot 2026-09-19 144221.png" alt="Multi-Service Concurrency Architecture" width="850">
</p>

### 🛡️ DevSecOps Pipeline Deep Dive (Single Service Lifecycle)

Every individual microservice follows a strict DevSecOps lifecycle before its image is cleared for deployment. This includes credential scanning, dependency building, and container vulnerability assessments.

<p align="center">
  <img src="./diagram/Screenshot 2026-09-19 144428.png" alt="Single Service DevSecOps Pipeline" width="850">
</p>

## 👨‍💻 Author
**Nishant Mishra**  
*Computer Science and Engineering*
Passionate about Platform Engineering, GitOps, DevOps, and building resilient distributed systems.