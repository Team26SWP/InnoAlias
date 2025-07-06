# InnoAlias Deployment Guide

This document explains how to deploy the complete InnoAlias stack using Docker Compose. The system consists of four containers: **backend**, **frontend**, **mongo**, and **nginx**. The provided `docker-compose.yml` orchestrates these services and is suitable for local testing as well as small production setups.

## 1. Prerequisites

- **Operating system**: Any platform that supports Docker (Ubuntu 20.04+ recommended)
- **Hardware**: 2 CPU cores and 4 GB of RAM minimum
- **Software**:
  - Docker Engine 20.10 or later
  - Docker Compose plugin

Clone the repository and switch to the project root:

```bash
git clone https://github.com/Team26SWP/InnoAlias.git
cd InnoAlias
```

## 2. Environment configuration

Copy the example environment file and adjust values as needed:

```bash
cp .env.example .env
```

Set the following variables inside `.env`:

- `SECRET_KEY` – random string used to sign JWTs (you can generate random key via command "openssl rand -base64 32")
- `ALGORITHM` – JWT algorithm (default `HS256`)
- `ACCESS_TOKEN_EXPIRE_MINUTES` – token lifetime
- `DOCKERHUB_USER` – Docker Hub user that hosts the prebuilt images
- `GEMINI_API_KEY` and `GEMINI_MODEL_NAME` – credentials for the AI game mode


## 3. Starting the stack

### Option A. You have prebuilt images (e.g. from CI) in docker hub

Pull the images and start all services in the background:

```bash
docker-compose pull
docker-compose up -d
```

After the containers are running you can verify their status with:

```bash
docker-compose ps
```

### Option B. You do not want to use CI, you want to build on the server

Just replace each `image:` line with a `build:` block that points at the directory containing the relevant Dockerfile:

```diff
 services:
   backend:
-    image: docker.io/${DOCKERHUB_USER}/innoalias-backend:latest
+    build:
+      context: ./backend
```

```diff
 services:
   frontend:
-    image: docker.io/${DOCKERHUB_USER}/innoalias-frontend:latest
+    build:
+      context: ./frontend
```

```diff
 services:
   nginx:
-    image: docker.io/${DOCKERHUB_USER}/innoalias-nginx:latest
+    build:
+      context: ./nginx
```

This step is necessary because right now docker-compose is configured for automatic deployment via CI/CD, but changing the strings will allow the project to be built locally.

After that, run
```bash
docker-compose up -d --build
```

You can verify status of containers via this command:

```bash
docker-compose ps
```




The frontend is served on port **80** by default. The backend API is reachable under `/api` via the Nginx reverse proxy.

MongoDB data is persisted in the `mongo-data` Docker volume. To remove all application data simply delete this volume:

```bash
docker volume rm innoalias_mongo-data
```

## 4. Updating

### Option A. You have prebuilt images (e.g. from CI) in docker hub

To fetch newer images and apply updates run:

```bash
docker-compose down
docker-compose pull
docker-compose up -d
```

This will recreate the containers using the latest images while preserving the MongoDB volume.

### Option B. You do not want to use CI, you want to build on the server

Just rebuild the containers:

```bash
docker-compose down
docker-compose up -d --build
```


After completing these steps the application should be available at `http://<host>` and ready for use.
