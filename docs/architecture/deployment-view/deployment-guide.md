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

### Option 2: Kubernetes Deployment

#### Step 1: Create Namespace

```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: innoalias
```

#### Step 2: Create ConfigMap

```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: innoalias-config
  namespace: innoalias
data:
  MONGO_URL: "mongodb://mongo:27017/"
  CORS_ORIGINS: '["http://localhost:3000"]'
```

#### Step 3: Create Secret

```yaml
# secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: innoalias-secret
  namespace: innoalias
type: Opaque
data:
  SECRET_KEY: <base64-encoded-secret>
  MONGO_ROOT_PASSWORD: <base64-encoded-password>
```

#### Step 4: Deploy Services

```bash
kubectl apply -f namespace.yaml
kubectl apply -f configmap.yaml
kubectl apply -f secret.yaml
kubectl apply -f k8s/
```

## Production Configuration

### Security Considerations

1. **Environment Variables**: Never commit secrets to version control
2. **Network Security**: Use firewalls to restrict access
3. **SSL/TLS**: Always use HTTPS in production
4. **Database Security**: Enable MongoDB authentication
5. **Container Security**: Regularly update base images

### Performance Optimization

1. **Resource Limits**: Set appropriate CPU/memory limits
2. **Database Indexing**: Create indexes on frequently queried fields
3. **Caching**: Consider Redis for session storage
4. **CDN**: Use CDN for static assets
5. **Load Balancing**: Implement horizontal scaling

### Monitoring Setup

#### Prometheus Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'innoalias-backend'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'
```

#### Grafana Dashboard

Import the provided Grafana dashboard configuration for monitoring:
- CPU/Memory usage
- Request latency
- Error rates
- Database performance

## Scaling Considerations

### Horizontal Scaling

1. **Backend Scaling**: Deploy multiple backend instances behind a load balancer
2. **Database Scaling**: Consider MongoDB replica sets for read scaling
3. **Frontend Scaling**: Use CDN for static content delivery

### Vertical Scaling

1. **Resource Allocation**: Increase CPU/memory based on usage patterns
2. **Database Optimization**: Add more storage and memory to MongoDB
3. **Network Optimization**: Use faster network connections

## Backup Strategy

### Database Backup

```bash
# Automated MongoDB backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker exec innoalias-mongo-1 mongodump --out /backup/$DATE
docker cp innoalias-mongo-1:/backup/$DATE ./backups/
```

### Application Backup

1. **Configuration**: Backup environment files and secrets
2. **Code**: Use Git for version control
3. **Docker Images**: Tag and store important image versions

## Troubleshooting

### Common Issues

1. **Container Won't Start**: Check logs with `docker-compose logs`
2. **Database Connection Issues**: Verify MongoDB is running and accessible
3. **WebSocket Issues**: Ensure nginx is properly configured for WebSocket proxy
4. **SSL Issues**: Verify certificate paths and permissions

### Health Checks

```bash
# Check all services
curl -f http://localhost/api/health || echo "Backend unhealthy"
curl -f http://localhost/ || echo "Frontend unhealthy"

# Check database
docker exec innoalias-mongo-1 mongosh --eval "db.adminCommand('ping')"
```

## Maintenance

### Regular Tasks

1. **Security Updates**: Monthly security patches
2. **Database Maintenance**: Weekly index optimization
3. **Log Rotation**: Daily log cleanup
4. **Backup Verification**: Weekly backup restoration tests

### Update Procedure

```bash
# Zero-downtime deployment
docker-compose pull
docker-compose up -d --no-deps backend
# Wait for health check
docker-compose up -d --no-deps frontend
docker-compose up -d --no-deps nginx
```

## Customer Deployment

### Self-Hosted Installation

1. **System Requirements**: Provide minimum hardware specifications
2. **Installation Script**: Create automated setup script
3. **Documentation**: Include user manual and troubleshooting guide
4. **Support**: Provide contact information for technical support

### Cloud Deployment

1. **AWS**: Use ECS/EKS with RDS for MongoDB
2. **Azure**: Use AKS with Azure Database for MongoDB
3. **GCP**: Use GKE with Cloud Firestore
4. **DigitalOcean**: Use App Platform or Kubernetes

### On-Premises Deployment

1. **Network Requirements**: Document firewall rules and ports
2. **Hardware Specifications**: Provide detailed hardware requirements
3. **Installation Guide**: Step-by-step installation instructions
4. **Maintenance Schedule**: Regular maintenance procedures 