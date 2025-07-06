# InnoAlias Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying the InnoAlias system in production environments. The system is designed to be containerized and can be deployed using Docker Compose or Kubernetes.

## Prerequisites

### System Requirements

- **CPU**: Minimum 2 cores, recommended 4+ cores
- **RAM**: Minimum 4GB, recommended 8GB+
- **Storage**: Minimum 20GB, recommended 50GB+ (for MongoDB data)
- **Network**: Stable internet connection for container image pulls

### Software Requirements

- **Docker**: Version 20.10+ with Docker Compose
- **Docker Hub Account**: For pulling container images
- **SSL Certificate**: For HTTPS in production (Let's Encrypt recommended)

## Deployment Options

### Option 1: Docker Compose (Recommended for Small-Medium Scale)

#### Step 1: Environment Setup

Create a `.env` file in the project root:

```bash
# Docker Hub Configuration
DOCKERHUB_USER=your-dockerhub-username

# Database Configuration
MONGO_URL=mongodb://mongo:27017/
MONGO_ROOT_USERNAME=admin
MONGO_ROOT_PASSWORD=secure_password_here

# JWT Configuration
SECRET_KEY=your-super-secret-jwt-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Application Configuration
CORS_ORIGINS=["http://localhost:3000", "https://yourdomain.com"]
```

#### Step 2: SSL Certificate Setup

For production, obtain SSL certificates:

```bash
# Using Let's Encrypt
sudo certbot certonly --standalone -d yourdomain.com
```

Update `nginx/nginx.conf` to include SSL configuration.

#### Step 3: Deploy

```bash
# Build and start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```
