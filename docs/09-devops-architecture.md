# DevOps & CI/CD Architecture
## Smart Crop Water Requirement Prediction System

---

## DevOps Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    DEVELOPMENT WORKFLOW                       │
│                                                              │
│  Developer                                                   │
│    │                                                         │
│    ├─→ Local Development (Docker Compose)                    │
│    │                                                         │
│    ├─→ Git Push                                              │
│    │                                                         │
│    ↓                                                         │
│  GitHub Repository                                           │
│    │                                                         │
│    ├─→ Feature Branch                                       │
│    │                                                         │
│    ├─→ Pull Request                                         │
│    │                                                         │
│    ↓                                                         │
│  Code Review                                                 │
│    │                                                         │
│    ├─→ Peer Review                                          │
│    │                                                         │
│    ├─→ Approval                                             │
│    │                                                         │
│    ↓                                                         │
│  Merge to Main Branch                                       │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    CI/CD PIPELINE                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Continuous Integration (CI)                           │  │
│  │  ┌────────────────────────────────────────────────┐   │  │
│  │  │  1. Trigger on Push/PR                         │   │  │
│  │  └────────────────────────────────────────────────┘   │  │
│  │  ┌────────────────────────────────────────────────┐   │  │
│  │  │  2. Code Quality Checks                        │   │  │
│  │  │     - Linting (Black, Flake8, Dart Lint)        │   │  │
│  │  │     - Formatting (Prettier, Black)              │   │  │
│  │  │     - Security Scanning (Snyk, SonarQube)       │   │  │
│  │  └────────────────────────────────────────────────┘   │  │
│  │  ┌────────────────────────────────────────────────┐   │  │
│  │  │  3. Unit Tests                                 │   │  │
│  │  │     - Backend Tests (pytest)                   │   │  │
│  │  │     - ML Tests (pytest)                        │   │  │
│  │  │     - Flutter Tests (flutter test)             │   │  │
│  │  └────────────────────────────────────────────────┘   │  │
│  │  ┌────────────────────────────────────────────────┐   │  │
│  │  │  4. Integration Tests                         │   │  │
│  │  │     - API Integration Tests                    │   │  │
│  │  │     - Database Integration Tests              │   │  │
│  │  └────────────────────────────────────────────────┘   │  │
│  │  ┌────────────────────────────────────────────────┐   │  │
│  │  │  5. Build Docker Images                       │   │  │
│  │  │     - Backend Image                            │   │  │
│  │  │     - ML Image                                 │   │  │
│  │  │     - Frontend Image (Web)                     │   │  │
│  │  └────────────────────────────────────────────────┘   │  │
│  │  ┌────────────────────────────────────────────────┐   │  │
│  │  │  6. Security Scanning                         │   │  │
│  │  │     - Docker Image Scanning (Trivy)           │   │  │
│  │  │     - Dependency Scanning (Snyk)               │   │  │
│  │  └────────────────────────────────────────────────┘   │  │
│  │  ┌────────────────────────────────────────────────┐   │  │
│  │  │  7. Push to Container Registry                │   │  │
│  │  │     - ECR/GCR/ACR                              │   │  │
│  │  └────────────────────────────────────────────────┘   │  │
│  └──────────────────────────────────────────────────────┘  │
│                           │                                  │
│                           ↓                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Continuous Deployment (CD)                         │  │
│  │  ┌────────────────────────────────────────────────┐   │  │
│  │  │  1. Deploy to Staging (on PR merge)            │   │  │
│  │  │     - Update Kubernetes Deployment             │   │  │
│  │  │     - Run Database Migrations                  │   │  │
│  │  │     - Health Checks                            │   │  │
│  │  │     - Smoke Tests                              │   │  │
│  │  └────────────────────────────────────────────────┘   │  │
│  │  ┌────────────────────────────────────────────────┐   │  │
│  │  │  2. Manual Approval for Production            │   │  │
│  │  │     - Notify Team                              │   │  │
│  │  │     - Wait for Approval                        │   │  │
│  │  └────────────────────────────────────────────────┘   │  │
│  │  ┌────────────────────────────────────────────────┐   │  │
│  │  │  3. Deploy to Production (on tag)              │   │  │
│  │  │     - Blue-Green Deployment                   │   │  │
│  │  │     - Database Migrations                     │   │  │
│  │  │     - Health Checks                            │   │  │
│  │  │     - Rollback on Failure                      │   │  │
│  │  └────────────────────────────────────────────────┘   │  │
│  └──────────────────────────────────────────────────────┘  │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    MONITORING & ALERTING                      │
│  - Application Performance Monitoring                       │
│  - Log Aggregation                                           │
│  - Error Tracking                                            │
│  - Uptime Monitoring                                         │
└─────────────────────────────────────────────────────────────┘
```

---

## CI/CD Pipeline Configuration

### GitHub Actions Workflow

#### Backend CI/CD Pipeline

```yaml
# .github/workflows/backend-ci.yml
name: Backend CI/CD

on:
  push:
    branches: [ main, develop ]
    paths:
      - 'backend/**'
      - '.github/workflows/backend-ci.yml'
  pull_request:
    branches: [ main ]
    paths:
      - 'backend/**'

env:
  PYTHON_VERSION: '3.11'
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}/backend

jobs:
  lint:
    name: Code Quality Checks
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      
      - name: Install dependencies
        run: |
          cd backend
          pip install black flake8 mypy pytest pytest-cov
      
      - name: Run Black
        run: |
          cd backend
          black --check .
      
      - name: Run Flake8
        run: |
          cd backend
          flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
      
      - name: Run MyPy
        run: |
          cd backend
          mypy app/

  test:
    name: Unit & Integration Tests
    runs-on: ubuntu-latest
    needs: lint
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      
      - name: Run tests
        run: |
          cd backend
          pytest tests/ -v --cov=app --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./backend/coverage.xml
          flags: backend

  security:
    name: Security Scanning
    runs-on: ubuntu-latest
    needs: test
    steps:
      - uses: actions/checkout@v3
      
      - name: Run Snyk Security Scan
        uses: snyk/actions/python@master
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
      
      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: 'backend'
          format: 'sarif'
          output: 'trivy-results.sarif'
      
      - name: Upload Trivy results to GitHub Security
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: 'trivy-results.sarif'

  build:
    name: Build Docker Image
    runs-on: ubuntu-latest
    needs: [test, security]
    outputs:
      image-tag: ${{ steps.meta.outputs.tags }}
      image-digest: ${{ steps.build.outputs.digest }}
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2
      
      - name: Log in to Container Registry
        uses: docker/login-action@v2
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v4
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=sha
      
      - name: Build and push Docker image
        id: build
        uses: docker/build-push-action@v4
        with:
          context: backend
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  deploy-staging:
    name: Deploy to Staging
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/develop'
    environment:
      name: staging
      url: https://staging-api.cropwater-prediction.com
    steps:
      - uses: actions/checkout@v3
      
      - name: Configure kubectl
        uses: azure/k8s-set-context@v3
        with:
          method: kubeconfig
          kubeconfig: ${{ secrets.STAGING_KUBECONFIG }}
      
      - name: Update Kubernetes deployment
        run: |
          kubectl set image deployment/backend-deployment \
            backend=${{ needs.build.outputs.image-tag }} \
            -n staging
      
      - name: Run database migrations
        run: |
          kubectl exec -n staging deployment/backend-deployment -- alembic upgrade head
      
      - name: Wait for rollout
        run: |
          kubectl rollout status deployment/backend-deployment -n staging --timeout=5m
      
      - name: Run smoke tests
        run: |
          curl -f https://staging-api.cropwater-prediction.com/api/v1/health || exit 1

  deploy-production:
    name: Deploy to Production
    runs-on: ubuntu-latest
    needs: build
    if: startsWith(github.ref, 'refs/tags/v')
    environment:
      name: production
      url: https://api.cropwater-prediction.com
    steps:
      - uses: actions/checkout@v3
      
      - name: Configure kubectl
        uses: azure/k8s-set-context@v3
        with:
          method: kubeconfig
          kubeconfig: ${{ secrets.PRODUCTION_KUBECONFIG }}
      
      - name: Blue-Green Deployment
        run: |
          # Deploy to green (new version)
          kubectl set image deployment/backend-deployment-green \
            backend=${{ needs.build.outputs.image-tag }} \
            -n production
          
          # Wait for green to be ready
          kubectl rollout status deployment/backend-deployment-green -n production --timeout=5m
          
          # Run smoke tests on green
          kubectl patch service backend-service-green -p '{"spec":{"selector":{"version":"green"}}}' -n production
          
          # Switch traffic to green
          kubectl patch service backend-service -p '{"spec":{"selector":{"version":"green"}}}' -n production
          
          # Wait for switch
          sleep 30
          
          # If successful, scale down blue
          kubectl scale deployment/backend-deployment-blue --replicas=0 -n production
      
      - name: Run database migrations
        run: |
          kubectl exec -n production deployment/backend-deployment-green -- alembic upgrade head
      
      - name: Rollback on failure
        if: failure()
        run: |
          kubectl patch service backend-service -p '{"spec":{"selector":{"version":"blue"}}}' -n production
          kubectl scale deployment/backend-deployment-green --replicas=0 -n production
```

#### Flutter CI/CD Pipeline

```yaml
# .github/workflows/flutter-ci.yml
name: Flutter CI/CD

on:
  push:
    branches: [ main, develop ]
    paths:
      - 'frontend/**'
      - '.github/workflows/flutter-ci.yml'
  pull_request:
    branches: [ main ]
    paths:
      - 'frontend/**'

env:
  FLUTTER_VERSION: '3.16.0'

jobs:
  lint:
    name: Code Quality Checks
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Flutter
        uses: subosito/flutter-action@v2
        with:
          flutter-version: ${{ env.FLUTTER_VERSION }}
          channel: 'stable'
      
      - name: Install dependencies
        run: |
          cd frontend
          flutter pub get
      
      - name: Run Flutter analyze
        run: |
          cd frontend
          flutter analyze
      
      - name: Run Dart format check
        run: |
          cd frontend
          dart format --set-exit-if-changed .

  test:
    name: Unit & Widget Tests
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Flutter
        uses: subosito/flutter-action@v2
        with:
          flutter-version: ${{ env.FLUTER_VERSION }}
          channel: 'stable'
      
      - name: Install dependencies
        run: |
          cd frontend
          flutter pub get
      
      - name: Run tests
        run: |
          cd frontend
          flutter test --coverage
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./frontend/coverage/lcov.info
          flags: flutter

  build-android:
    name: Build Android APK
    runs-on: ubuntu-latest
    needs: test
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Flutter
        uses: subosito/flutter-action@v2
        with:
          flutter-version: ${{ env.FLUTER_VERSION }}
          channel: 'stable'
      
      - name: Install dependencies
        run: |
          cd frontend
          flutter pub get
      
      - name: Build APK
        run: |
          cd frontend
          flutter build apk --release
      
      - name: Upload APK
        uses: actions/upload-artifact@v3
        with:
          name: android-apk
          path: frontend/build/app/outputs/flutter-apk/app-release.apk

  build-web:
    name: Build Web Version
    runs-on: ubuntu-latest
    needs: test
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Flutter
        uses: subosito/flutter-action@v2
        with:
          flutter-version: ${{ env.FLUTER_VERSION }}
          channel: 'stable'
      
      - name: Install dependencies
        run: |
          cd frontend
          flutter pub get
      
      - name: Build web
        run: |
          cd frontend
          flutter build web --release
      
      - name: Upload web build
        uses: actions/upload-artifact@v3
        with:
          name: web-build
          path: frontend/build/web

  deploy-web-staging:
    name: Deploy Web to Staging
    runs-on: ubuntu-latest
    needs: build-web
    if: github.ref == 'refs/heads/develop'
    environment:
      name: staging
      url: https://staging.cropwater-prediction.com
    steps:
      - uses: actions/download-artifact@v3
        with:
          name: web-build
          path: ./build
      
      - name: Deploy to Cloud Storage
        uses: jakejarvis/s3-sync-action@master
        with:
          args: --acl public-read --delete
        env:
          AWS_S3_BUCKET: ${{ secrets.STAGING_S3_BUCKET }}
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          AWS_REGION: 'us-east-1'
          SOURCE_DIR: 'build'

  deploy-web-production:
    name: Deploy Web to Production
    runs-on: ubuntu-latest
    needs: build-web
    if: startsWith(github.ref, 'refs/tags/v')
    environment:
      name: production
      url: https://cropwater-prediction.com
    steps:
      - uses: actions/download-artifact@v3
        with:
          name: web-build
          path: ./build
      
      - name: Deploy to Cloud Storage
        uses: jakejarvis/s3-sync-action@master
        with:
          args: --acl public-read --delete
        env:
          AWS_S3_BUCKET: ${{ secrets.PRODUCTION_S3_BUCKET }}
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          AWS_REGION: 'us-east-1'
          SOURCE_DIR: 'build'
      
      - name: Invalidate CloudFront cache
        uses: awslabs/amazon-cloudfront-invalidate-cache@master
        env:
          DISTRIBUTION_ID: ${{ secrets.CLOUDFRONT_DISTRIBUTION_ID }}
          PATHS: '/*'
```

#### ML Pipeline CI/CD

```yaml
# .github/workflows/ml-ci.yml
name: ML Pipeline CI/CD

on:
  push:
    branches: [ main, develop ]
    paths:
      - 'ml/**'
      - 'datasets/**'
      - '.github/workflows/ml-ci.yml'
  pull_request:
    branches: [ main ]
    paths:
      - 'ml/**'
      - 'datasets/**'

env:
  PYTHON_VERSION: '3.11'

jobs:
  data-validation:
    name: Dataset Validation
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      
      - name: Install dependencies
        run: |
          cd ml
          pip install -r requirements.txt
      
      - name: Validate datasets
        run: |
          cd ml
          python scripts/validate_datasets.py
      
      - name: Generate data quality report
        run: |
          cd ml
          python scripts/generate_quality_report.py
      
      - name: Upload quality report
        uses: actions/upload-artifact@v3
        with:
          name: quality-report
          path: ml/reports/quality_report.html

  train-model:
    name: Train ML Model
    runs-on: ubuntu-latest
    needs: data-validation
    if: github.ref == 'refs/heads/main' || github.ref == 'refs/heads/develop'
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      
      - name: Install dependencies
        run: |
          cd ml
          pip install -r requirements.txt
      
      - name: Run training pipeline
        run: |
          cd ml
          python training/train.py
      
      - name: Generate evaluation report
        run: |
          cd ml
          python evaluation/generate_report.py
      
      - name: Upload model
        uses: actions/upload-artifact@v3
        with:
          name: trained-model
          path: ml/saved_models/
      
      - name: Upload evaluation report
        uses: actions/upload-artifact@v3
        with:
          name: evaluation-report
          path: ml/reports/evaluation_report.html

  deploy-model:
    name: Deploy Model to Production
    runs-on: ubuntu-latest
    needs: train-model
    if: github.ref == 'refs/heads/main'
    environment:
      name: production
    steps:
      - uses: actions/download-artifact@v3
        with:
          name: trained-model
          path: ./models
      
      - name: Upload to Object Storage
        run: |
          aws s3 sync ./models s3://cwr-system/models/ --delete
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          AWS_REGION: 'us-east-1'
      
      - name: Trigger model reload
        run: |
          curl -X POST https://api.cropwater-prediction.com/api/v1/admin/reload-model \
            -H "Authorization: Bearer ${{ secrets.ADMIN_API_KEY }}"
```

---

## Docker Configuration

### Docker Compose for Local Development

```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: cwr_db
      POSTGRES_USER: cwr_user
      POSTGRES_PASSWORD: cwr_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U cwr_user -d cwr_db"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://cwr_user:cwr_password@postgres:5432/cwr_db
      REDIS_URL: redis://redis:6379
      WEATHER_API_KEY: ${WEATHER_API_KEY}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./backend:/app
      - ./datasets:/datasets
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  ml:
    build:
      context: ./ml
      dockerfile: Dockerfile
    volumes:
      - ./ml:/app
      - ./datasets:/datasets
      - ./ml/saved_models:/app/saved_models
    environment:
      DATABASE_URL: postgresql://cwr_user:cwr_password@postgres:5432/cwr_db
    depends_on:
      - postgres
    command: python -m jupyter notebook --ip=0.0.0.0 --port=8888 --allow-root

volumes:
  postgres_data:
```

---

## Kubernetes Configuration

### Namespace Configuration

```yaml
# k8s/namespaces.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: development
---
apiVersion: v1
kind: Namespace
metadata:
  name: staging
---
apiVersion: v1
kind: Namespace
metadata:
  name: production
```

### ConfigMap Configuration

```yaml
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: backend-config
  namespace: production
data:
  APP_ENV: "production"
  LOG_LEVEL: "info"
  CACHE_TTL: "900"
  MAX_UPLOAD_SIZE: "10485760"
```

### Secret Configuration

```yaml
# k8s/secrets.yaml (example - use external secret manager in production)
apiVersion: v1
kind: Secret
metadata:
  name: backend-secrets
  namespace: production
type: Opaque
stringData:
  database-url: "postgresql://user:password@postgres-primary:5432/cwr_db"
  redis-url: "redis://redis:6379"
  weather-api-key: "your-api-key"
  jwt-secret: "your-jwt-secret"
  secret-key: "your-secret-key"
```

---

## Monitoring & Observability

### Prometheus Configuration

```yaml
# k8s/prometheus-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
      evaluation_interval: 15s
    
    scrape_configs:
      - job_name: 'backend'
        kubernetes_sd_configs:
          - role: pod
        relabel_configs:
          - source_labels: [__meta_kubernetes_pod_label_app]
            action: keep
            regex: backend
          - source_labels: [__meta_kubernetes_pod_ip]
            target_label: __address__
            replacement: $1:8000
      
      - job_name: 'postgres'
        static_configs:
          - targets: ['postgres-exporter:9187']
```

### Grafana Dashboards

**Key Dashboards**:
1. **API Performance Dashboard**
   - Request rate
   - Response time (p50, p95, p99)
   - Error rate
   - Status code distribution

2. **Database Dashboard**
   - Connection pool usage
   - Query performance
   - Transaction rate
   - Replication lag

3. **ML Model Dashboard**
   - Prediction latency
   - Prediction rate
   - Model accuracy over time
   - Feature distribution drift

4. **System Resources Dashboard**
   - CPU usage
   - Memory usage
   - Disk usage
   - Network I/O

---

## Logging Strategy

### Structured Logging

```python
# backend/app/core/logging.py
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
        
        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id
        
        return json.dumps(log_data)

def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)
    
    return logger
```

---

## Testing Strategy

### Test Pyramid

```
        /\
       /E2E\          (10%)
      /------\
     /Integration\    (30%)
    /------------\
   /   Unit Tests  \  (60%)
  /----------------\
```

### Unit Tests

**Backend (pytest)**:
```python
# tests/unit/test_prediction_service.py
import pytest
from app.services.prediction_service import PredictionService

def test_calculate_cwr():
    service = PredictionService()
    result = service.calculate_cwr(
        temperature=28.0,
        humidity=65.0,
        kc_value=1.2
    )
    assert result['cwr_mm_day'] > 0
    assert result['cwr_mm_day'] < 10
```

**Flutter (flutter test)**:
```dart
// test/unit/prediction_test.dart
import 'package:flutter_test/flutter_test.dart';
import 'package:cwr_app/models/prediction.dart';

void main() {
  test('CWR calculation should return positive value', () {
    final prediction = Prediction(
      temperature: 28.0,
      humidity: 65.0,
      kcValue: 1.2,
    );
    expect(prediction.cwrMMDay, greaterThan(0));
  });
}
```

### Integration Tests

```python
# tests/integration/test_api.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_predict_cwr():
    response = client.post(
        "/api/v1/predictions/cwr",
        json={
            "field_crop_id": 1,
            "prediction_date": "2024-06-20"
        },
        headers={"Authorization": "Bearer test-token"}
    )
    assert response.status_code == 200
    assert "cwr_mm_day" in response.json()
```

### E2E Tests

```python
# tests/e2e/test_user_flow.py
from selenium import webdriver
from selenium.webdriver.common.by import By

def test_complete_prediction_flow():
    driver = webdriver.Chrome()
    
    try:
        # Login
        driver.get("https://staging.cropwater-prediction.com")
        driver.find_element(By.ID, "email").send_keys("test@example.com")
        driver.find_element(By.ID, "password").send_keys("password")
        driver.find_element(By.ID, "login-btn").click()
        
        # Navigate to prediction
        driver.find_element(By.ID, "prediction-tab").click()
        
        # Select crop
        driver.find_element(By.ID, "crop-select").click()
        driver.find_element(By.XPATH, "//option[text()='Paddy']").click()
        
        # Submit prediction
        driver.find_element(By.ID, "predict-btn").click()
        
        # Verify result
        assert "CWR" in driver.page_source
        
    finally:
        driver.quit()
```

---

## Git Strategy

### Branching Strategy

```
main (production)
  ↑
  │
develop (staging)
  ↑
  │
feature/* (feature branches)
  ↑
  │
hotfix/* (hotfix branches)
```

### Branch Naming Conventions

- `feature/cwr-prediction-api`
- `feature/flutter-dashboard`
- `bugfix/weather-api-timeout`
- `hotfix/security-patch`
- `refactor/database-optimization`

### Commit Message Conventions

```
feat: add CWR prediction API endpoint
fix: resolve weather API timeout issue
docs: update API documentation
style: format code with black
refactor: simplify prediction service
test: add unit tests for prediction service
chore: update dependencies
```

---

## Key Design Decisions

### 1. GitHub Actions for CI/CD
- **Reason**: Native GitHub integration, free for public repos, extensive marketplace
- **Implementation**: Separate workflows for backend, frontend, and ML

### 2. Docker for Containerization
- **Reason**: Consistency across environments, easy deployment
- **Implementation**: Multi-stage Dockerfiles for optimization

### 3. Kubernetes for Orchestration
- **Reason**: Scalability, self-healing, portability
- **Implementation**: EKS/GKE/AKS depending on cloud provider

### 4. Blue-Green Deployment
- **Reason**: Zero-downtime deployments, easy rollback
- **Implementation**: Two production deployments with traffic switching

### 5. Automated Testing
- **Reason**: Catch bugs early, ensure quality
- **Implementation**: Unit, integration, and E2E tests in CI pipeline

### 6. Security Scanning
- **Reason**: Identify vulnerabilities early
- **Implementation**: Snyk, Trivy, and dependency scanning

### 7. Monitoring & Alerting
- **Reason**: Observability, quick incident response
- **Implementation**: Prometheus, Grafana, and alerting rules

### 8. Structured Logging
- **Reason**: Easy log parsing and analysis
- **Implementation**: JSON-formatted logs with correlation IDs

### 9. Environment Separation
- **Reason**: Isolation, testing before production
- **Implementation**: Development, staging, and production environments

### 10. Git Flow Branching Strategy
- **Reason**: Organized development, clear release process
- **Implementation**: Feature branches, develop branch, main branch
