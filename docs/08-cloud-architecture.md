# Cloud Deployment Architecture
## Smart Crop Water Requirement Prediction System

---

## Cloud Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      USER LAYER                               │
│  ┌──────────────────┐  ┌──────────────────┐                 │
│  │  Flutter App    │  │  Web Browser     │                 │
│  │  (Android)       │  │  (Responsive)    │                 │
│  └──────────────────┘  └──────────────────┘                 │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            │ HTTPS
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    CLOUD PROVIDER (AWS/GCP/Azure)              │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              CDN / EDGE LOCATIONS                      │  │
│  │  - Static assets (Flutter web build)                  │  │
│  │  - API caching                                         │  │
│  │  - Content distribution                               │  │
│  └──────────────────────────────────────────────────────┘  │
│                           │                                  │
│                           ↓                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              LOAD BALANCER / API GATEWAY               │  │
│  │  - SSL termination                                    │  │
│  │  - Request routing                                    │  │
│  │  - Rate limiting                                      │  │
│  │  - Health checks                                      │  │
│  └──────────────────────────────────────────────────────┘  │
│                           │                                  │
│        ┌──────────────────┼──────────────────┐              │
│        │                  │                  │              │
│        ↓                  ↓                  ↓              │
│  ┌──────────┐      ┌──────────┐      ┌──────────┐        │
│  │  Backend │      │  Backend │      │  Backend │        │
│  │  Pod 1   │      │  Pod 2   │      │  Pod N   │        │
│  │ (FastAPI)│      │ (FastAPI)│      │ (FastAPI)│        │
│  └──────────┘      └──────────┘      └──────────┘        │
│        │                  │                  │              │
│        └──────────────────┼──────────────────┘              │
│                           │                                  │
│                           ↓                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              KUBERNETES CLUSTER (K8s)                   │  │
│  │  - Container orchestration                           │  │
│  │  - Auto-scaling                                       │  │
│  │  - Service discovery                                  │  │
│  │  - Self-healing                                       │  │
│  └──────────────────────────────────────────────────────┘  │
│                           │                                  │
│        ┌──────────────────┼──────────────────┐              │
│        ↓                  ↓                  ↓              │
│  ┌──────────┐      ┌──────────┐      ┌──────────┐        │
│  │PostgreSQL│      │  Redis   │      │  Object  │        │
│  │ Primary  │      │  Cache   │      │  Storage │        │
│  └────┬─────┘      └──────────┘      └──────────┘        │
│       │                                       │              │
│       ↓                                       ↓              │
│  ┌──────────┐                          ┌──────────┐        │
│  │PostgreSQL│                          │  ML Model│        │
│  │ Replica  │                          │  Storage │        │
│  └──────────┘                          └──────────┘        │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              MONITORING & LOGGING                     │  │
│  │  - Metrics (Prometheus/Grafana)                       │  │
│  │  - Logs (CloudWatch/Stackdriver)                      │  │
│  │  - Tracing (Jaeger/X-Ray)                             │  │
│  │  - Alerts (PagerDuty/Slack)                           │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              SECURITY SERVICES                         │  │
│  │  - WAF (Web Application Firewall)                     │  │
│  │  - DDoS Protection                                    │  │
│  │  - Secret Manager                                     │  │
│  │  - IAM (Identity & Access Management)                 │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## Cloud Provider Options

### Option 1: AWS (Amazon Web Services)

**Components**:
- **EKS**: Elastic Kubernetes Service for container orchestration
- **RDS**: PostgreSQL for managed database
- **ElastiCache**: Redis for caching
- **S3**: Object storage for datasets and ML models
- **CloudFront**: CDN for static assets
- **ALB**: Application Load Balancer
- **Route 53**: DNS management
- **CloudWatch**: Monitoring and logging
- **Secrets Manager**: Secret management
- **WAF**: Web Application Firewall

**Architecture Diagram (AWS)**:
```
┌─────────────────────────────────────────────────────────────┐
│                        AWS CLOUD                             │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  CloudFront (CDN)                                      │  │
│  └──────────────────────────────────────────────────────┘  │
│                           │                                  │
│                           ↓                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Application Load Balancer (ALB)                       │  │
│  └──────────────────────────────────────────────────────┘  │
│                           │                                  │
│                           ↓                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Amazon EKS (Kubernetes Cluster)                     │  │
│  │  ┌──────────────┐  ┌──────────────┐                  │  │
│  │  │ FastAPI Pod  │  │ FastAPI Pod  │                  │  │
│  │  └──────────────┘  └──────────────┘                  │  │
│  └──────────────────────────────────────────────────────┘  │
│                           │                                  │
│        ┌──────────────────┼──────────────────┐              │
│        ↓                  ↓                  ↓              │
│  ┌──────────┐      ┌──────────┐      ┌──────────┐        │
│  │Amazon RDS│      │ElastiCache│     │Amazon S3 │        │
│  │PostgreSQL│      │  Redis   │     │  Storage │        │
│  └──────────┘      └──────────┘      └──────────┘        │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  CloudWatch (Monitoring)                              │  │
│  │  Secrets Manager (Secrets)                            │  │
│  │  WAF (Security)                                       │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

### Option 2: Google Cloud Platform (GCP)

**Components**:
- **GKE**: Google Kubernetes Engine for container orchestration
- **Cloud SQL**: PostgreSQL for managed database
- **Memorystore**: Redis for caching
- **Cloud Storage**: Object storage for datasets and ML models
- **Cloud CDN**: CDN for static assets
- **Cloud Load Balancing**: Load balancing
- **Cloud DNS**: DNS management
- **Cloud Monitoring**: Monitoring and logging
- **Secret Manager**: Secret management
- **Cloud Armor**: Web Application Firewall

**Architecture Diagram (GCP)**:
```
┌─────────────────────────────────────────────────────────────┐
│                       GCP CLOUD                              │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Cloud CDN                                             │  │
│  └──────────────────────────────────────────────────────┘  │
│                           │                                  │
│                           ↓                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Cloud Load Balancing                                 │  │
│  └──────────────────────────────────────────────────────┘  │
│                           │                                  │
│                           ↓                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Google Kubernetes Engine (GKE)                      │  │
│  │  ┌──────────────┐  ┌──────────────┐                  │  │
│  │  │ FastAPI Pod  │  │ FastAPI Pod  │                  │  │
│  │  └──────────────┘  └──────────────┘                  │  │
│  └──────────────────────────────────────────────────────┘  │
│                           │                                  │
│        ┌──────────────────┼──────────────────┐              │
│        ↓                  ↓                  ↓              │
│  ┌──────────┐      ┌──────────┐      ┌──────────┐        │
│  │Cloud SQL │      │Memorystore│    │Cloud     │        │
│  │PostgreSQL│      │  Redis   │    │Storage   │        │
│  └──────────┘      └──────────┘      └──────────┘        │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Cloud Monitoring (Monitoring)                         │  │
│  │  Secret Manager (Secrets)                              │  │
│  │  Cloud Armor (Security)                                │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

### Option 3: Azure (Microsoft Azure)

**Components**:
- **AKS**: Azure Kubernetes Service for container orchestration
- **Azure Database for PostgreSQL**: Managed database
- **Azure Cache for Redis**: Redis for caching
- **Blob Storage**: Object storage for datasets and ML models
- **Azure CDN**: CDN for static assets
- **Azure Load Balancer**: Load balancing
- **Azure DNS**: DNS management
- **Azure Monitor**: Monitoring and logging
- **Azure Key Vault**: Secret management
- **Azure WAF**: Web Application Firewall

---

## Deployment Architecture Details

### 1. Container Strategy

**Docker Images**:
```dockerfile
# Backend Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```dockerfile
# Frontend Dockerfile (for web deployment)
FROM ubuntu:latest

# Install Flutter dependencies
RUN apt-get update && apt-get install -y \
    curl git unzip xz-utils zip libglu1-mesa \
    && rm -rf /var/lib/apt/lists/*

# Install Flutter
RUN git clone https://github.com/flutter/flutter.git -b stable /opt/flutter
ENV PATH="/opt/flutter/bin:${PATH}"
RUN flutter doctor

# Build web app
COPY . /app
WORKDIR /app
RUN flutter pub get
RUN flutter build web

# Serve with nginx
FROM nginx:alpine
COPY --from=0 /app/build/web /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

**Kubernetes Deployment (Backend)**:
```yaml
# k8s/backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend-deployment
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: your-registry/backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: backend-secrets
              key: database-url
        - name: WEATHER_API_KEY
          valueFrom:
            secretKeyRef:
              name: backend-secrets
              key: weather-api-key
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: backend-service
spec:
  selector:
    app: backend
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

---

### 2. Database Architecture

**Primary-Replica Setup**:
```yaml
# k8s/postgres-primary.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres-primary
spec:
  serviceName: postgres-primary
  replicas: 1
  selector:
    matchLabels:
      app: postgres-primary
  template:
    metadata:
      labels:
        app: postgres-primary
    spec:
      containers:
      - name: postgres
        image: postgres:15
        env:
        - name: POSTGRES_DB
          value: cwr_db
        - name: POSTGRES_USER
          valueFrom:
            secretKeyRef:
              name: postgres-secrets
              key: username
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-secrets
              key: password
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:
  - metadata:
      name: postgres-storage
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 100Gi
```

**Connection Pooling**:
- Use PgBouncer for connection pooling
- Configure pool size based on load
- Implement connection timeouts

**Backup Strategy**:
- Automated daily backups
- Point-in-time recovery (PITR)
- Cross-region replication for disaster recovery

---

### 3. Caching Strategy

**Redis Configuration**:
```yaml
# k8s/redis-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis-deployment
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
        command: ["redis-server", "--maxmemory", "256mb", "--maxmemory-policy", "allkeys-lru"]
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

**Cache Strategy**:
- Weather API responses: 15 minutes TTL
- Crop data: 1 hour TTL
- Soil data: 24 hours TTL
- Model predictions: 5 minutes TTL

---

### 4. Object Storage Strategy

**S3/GCS Bucket Structure**:
```
cwr-system/
├── datasets/
│   ├── crop/
│   ├── soil/
│   ├── weather/
│   └── rainfall/
├── models/
│   ├── baseline_model.pkl
│   ├── best_model.pkl
│   └── model_metadata.json
├── backups/
│   ├── database/
│   └── config/
└── static/
    └── flutter-web/
```

**Access Control**:
- IAM roles for service accounts
- Bucket policies for public/private access
- Pre-signed URLs for temporary access

---

### 5. Auto-scaling Strategy

**Horizontal Pod Autoscaler (HPA)**:
```yaml
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend-deployment
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

**Cluster Autoscaler**:
- Scale cluster nodes based on pod resource requests
- Scale down underutilized nodes
- Configure node pools for different workloads

---

### 6. Monitoring Architecture

**Prometheus + Grafana Stack**:
```yaml
# k8s/prometheus-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: prometheus
spec:
  replicas: 1
  selector:
    matchLabels:
      app: prometheus
  template:
    metadata:
      labels:
        app: prometheus
    spec:
      containers:
      - name: prometheus
        image: prom/prometheus:latest
        ports:
        - containerPort: 9090
        volumeMounts:
        - name: prometheus-config
          mountPath: /etc/prometheus
        - name: prometheus-storage
          mountPath: /prometheus
```

**Metrics to Monitor**:
- API response times
- Request rates
- Error rates
- Database connection pool usage
- Cache hit/miss ratios
- Pod resource utilization
- Prediction latency

**Alerting Rules**:
```yaml
# prometheus-alerts.yaml
groups:
- name: api_alerts
  rules:
  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
    for: 5m
    annotations:
      summary: "High error rate detected"
  
  - alert: SlowResponseTime
    expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1
    for: 5m
    annotations:
      summary: "95th percentile response time too high"
  
  - alert: HighDatabaseConnections
    expr: pg_stat_activity_count > 80
    for: 5m
    annotations:
      summary: "Database connection pool nearly exhausted"
```

---

### 7. Logging Architecture

**Centralized Logging**:
- Application logs → CloudWatch Logs / Cloud Logging
- Access logs → CloudWatch Logs / Cloud Logging
- Audit logs → CloudTrail / Cloud Audit Logs

**Log Retention**:
- Application logs: 30 days
- Access logs: 90 days
- Audit logs: 1 year

---

### 8. Security Architecture

**Network Security**:
- VPC with private subnets for databases
- Security groups with least privilege
- Network policies in Kubernetes
- TLS/SSL for all communications

**Secrets Management**:
```yaml
# k8s/secrets.yaml (example - use external secret manager in production)
apiVersion: v1
kind: Secret
metadata:
  name: backend-secrets
type: Opaque
stringData:
  database-url: "postgresql://user:password@postgres-primary:5432/cwr_db"
  weather-api-key: "your-api-key"
  jwt-secret: "your-jwt-secret"
```

**IAM Roles**:
- Separate roles for each service
- Least privilege principle
- Regular access reviews

**WAF Rules**:
- SQL injection protection
- XSS protection
- Rate limiting
- IP whitelisting/blacklisting

---

### 9. Disaster Recovery

**Backup Strategy**:
- Database: Daily automated backups, 30-day retention
- Object storage: Versioning enabled, cross-region replication
- Configuration: Git version control

**Recovery Time Objectives (RTO)**:
- Critical services: 1 hour
- Non-critical services: 4 hours

**Recovery Point Objectives (RPO)**:
- Database: 15 minutes
- Object storage: Real-time replication

---

### 10. Cost Optimization

**Cost Optimization Strategies**:
- Use spot instances for non-critical workloads
- Auto-scaling to scale down during low traffic
- Reserved instances for baseline capacity
- S3 lifecycle policies for data archival
- CDN caching to reduce API calls

**Cost Monitoring**:
- Set budget alerts
- Monitor cost per service
- Identify cost anomalies

---

## Environment Configuration

### Development Environment
- Local development with Docker Compose
- Local PostgreSQL instance
- Mock weather API
- No auto-scaling
- Basic monitoring

### Staging Environment
- Small cloud deployment
- Managed PostgreSQL (dev tier)
- Real weather API (test key)
- Basic auto-scaling
- Full monitoring stack

### Production Environment
- Full cloud deployment
- Managed PostgreSQL (production tier)
- Real weather API (production key)
- Full auto-scaling
- Full monitoring and alerting
- Disaster recovery enabled

---

## Deployment Pipeline

### CI/CD Integration
```
Developer Push
    ↓
GitHub Repository
    ↓
CI Pipeline (GitHub Actions)
    ↓
Build Docker Images
    ↓
Run Tests
    ↓
Push to Container Registry
    ↓
CD Pipeline
    ↓
Update Kubernetes Deployment
    ↓
Health Checks
    ↓
Rollout Complete
```

---

## Key Design Decisions

### 1. Kubernetes for Orchestration
- **Reason**: Scalability, self-healing, portability
- **Implementation**: EKS/GKE/AKS depending on cloud provider

### 2. Managed Database Service
- **Reason**: Reduced operational overhead, automated backups, high availability
- **Implementation**: RDS/Cloud SQL/Azure Database

### 3. Redis for Caching
- **Reason**: Reduce database load, improve API response times
- **Implementation**: ElastiCache/Memorystore/Azure Cache

### 4. Object Storage for Datasets/Models
- **Reason**: Scalable storage, easy access, versioning
- **Implementation**: S3/Cloud Storage/Blob Storage

### 5. CDN for Static Assets
- **Reason**: Global content delivery, reduced latency
- **Implementation**: CloudFront/Cloud CDN/Azure CDN

### 6. Secret Manager
- **Reason**: Secure secret storage, rotation, audit
- **Implementation**: Secrets Manager/Secret Manager/Key Vault

### 7. Auto-scaling
- **Reason**: Handle variable load, cost optimization
- **Implementation**: HPA + Cluster Autoscaler

### 8. Monitoring Stack
- **Reason**: Observability, alerting, debugging
- **Implementation**: Prometheus + Grafana + CloudWatch/Cloud Monitoring

### 9. Multi-environment Setup
- **Reason**: Isolation, testing before production
- **Implementation**: Separate clusters/namespaces for dev/staging/prod

### 10. Disaster Recovery
- **Reason**: Business continuity, data protection
- **Implementation**: Backups, replication, failover procedures
