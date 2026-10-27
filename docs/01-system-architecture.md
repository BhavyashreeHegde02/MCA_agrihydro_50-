# Smart Crop Water Requirement Prediction System
## Complete System Architecture

---

## 1. High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     FARMER (End User)                            │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            │ Flutter App (Android + Web)
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                    FLUTTER FRONTEND                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  Auth Module │  │  Farm Module │  │  CWR Module  │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  Weather UI  │  │  Advisory UI │  │  Analytics   │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            │ REST API (HTTPS)
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                    CLOUD INFRASTRUCTURE                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              LOAD BALANCER / API GATEWAY                  │  │
│  └───────────────────────────┬──────────────────────────────┘  │
│                              │                                   │
│  ┌───────────────────────────┴──────────────────────────────┐  │
│  │                    FASTAPI BACKEND                         │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │  │
│  │  │ Auth Service │  │ Farm Service │  │ CWR Service  │   │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘   │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │  │
│  │  │Weather Service│ │Soil Service  │ │ Advisory Svc  │   │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘   │  │
│  └───────────────────────────┬──────────────────────────────┘  │
│                              │                                   │
│  ┌───────────────────────────┴──────────────────────────────┐  │
│  │                  ML INFERENCE SERVICE                     │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │  │
│  │  │Feature Eng.  │  │ Model Loader │  │ Prediction   │   │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘   │  │
│  └───────────────────────────┬──────────────────────────────┘  │
└──────────────────────────────┼─────────────────────────────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
        ↓                      ↓                      ↓
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│  PostgreSQL   │    │  Object Store │    │  Weather API  │
│   Database    │    │ (Datasets/    │    │  (External)   │
│               │    │  Models)      │    │               │
└───────────────┘    └───────────────┘    └───────────────┘
```

---

## 2. Component Architecture

### 2.1 Flutter Frontend Architecture

```
lib/
├── main.dart
├── app.dart
├── config/
│   ├── api_config.dart
│   ├── app_config.dart
│   └── theme_config.dart
├── core/
│   ├── constants/
│   ├── utils/
│   ├── validators/
│   └── exceptions/
├── data/
│   ├── models/
│   ├── repositories/
│   └── services/
│       ├── api_service.dart
│       ├── auth_service.dart
│       └── storage_service.dart
├── domain/
│   ├── entities/
│   └── usecases/
├── presentation/
│   ├── pages/
│   ├── widgets/
│   ├── providers/
│   └── screens/
└── routes/
```

**Key Flutter Modules:**
- **Authentication**: Login, Register, Password Management
- **Farm Management**: Farm CRUD, Field Management
- **Crop Management**: Crop Selection, Growth Stage Selection
- **Soil Management**: Soil Data Entry, Soil Information Display
- **Weather Module**: Current Weather, Forecast, Historical Weather
- **CWR Prediction**: Prediction Input, Result Display, Explanation
- **Irrigation Module**: Irrigation Calculator, Advisory Display
- **Water Use Tracking**: Irrigation Event Recording, Usage Analytics
- **Analytics Dashboard**: Charts, Trends, Historical Analysis
- **Data Quality**: Anomaly Alerts, Data Validation Status
- **Admin/Research**: Model Performance, Dataset Statistics

### 2.2 FastAPI Backend Architecture

```
backend/
├── app/
│   ├── main.py
│   ├── config/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── endpoints/
│   │   │   │   ├── auth.py
│   │   │   │   ├── farms.py
│   │   │   │   ├── crops.py
│   │   │   │   ├── soil.py
│   │   │   │   ├── weather.py
│   │   │   │   ├── predictions.py
│   │   │   │   ├── irrigation.py
│   │   │   │   ├── water_use.py
│   │   │   │   ├── analytics.py
│   │   │   │   ├── advisory.py
│   │   │   │   ├── data_quality.py
│   │   │   │   └── admin.py
│   │   │   └── api.py
│   │   └── deps.py
│   ├── core/
│   │   ├── security.py
│   │   ├── config.py
│   │   └── exceptions.py
│   ├── models/
│   │   ├── user.py
│   │   ├── farmer.py
│   │   ├── farm.py
│   │   ├── crop.py
│   │   ├── soil.py
│   │   ├── weather.py
│   │   ├── prediction.py
│   │   └── irrigation.py
│   ├── schemas/
│   │   ├── user.py
│   │   ├── farmer.py
│   │   ├── farm.py
│   │   ├── crop.py
│   │   ├── soil.py
│   │   ├── weather.py
│   │   ├── prediction.py
│   │   └── irrigation.py
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── farm_service.py
│   │   ├── crop_service.py
│   │   ├── soil_service.py
│   │   ├── weather_service.py
│   │   ├── prediction_service.py
│   │   ├── irrigation_service.py
│   │   ├── advisory_service.py
│   │   ├── anomaly_service.py
│   │   └── ml_service.py
│   ├── database/
│   │   ├── connection.py
│   │   ├── base.py
│   │   └── repositories/
│   └── ml/
│       ├── inference.py
│       ├── feature_engineering.py
│       └── model_loader.py
├── tests/
├── alembic/
└── requirements.txt
```

**Key Backend Services:**
- **AuthService**: JWT authentication, user management
- **FarmService**: Farm and field CRUD operations
- **CropService**: Crop data, growth stage management
- **SoilService**: Soil data retrieval and management
- **WeatherService**: Weather API integration, caching
- **PredictionService**: CWR prediction orchestration
- **IrrigationService**: Irrigation requirement calculation
- **AdvisoryService**: Farmer advisory generation
- **AnomalyService**: Data quality anomaly detection
- **MLService**: ML model inference and feature engineering

### 2.3 ML Pipeline Architecture

```
ml/
├── data/
│   ├── raw/
│   ├── processed/
│   ├── features/
│   └── splits/
├── preprocessing/
│   ├── data_loader.py
│   ├── data_cleaner.py
│   ├── missing_value_handler.py
│   ├── outlier_detector.py
│   └── data_validator.py
├── feature_engineering/
│   ├── weather_features.py
│   ├── soil_features.py
│   ├── crop_features.py
│   ├── temporal_features.py
│   ├── feature_selector.py
│   └── feature_scaler.py
├── models/
│   ├── baseline.py
│   ├── linear_regression.py
│   ├── random_forest.py
│   ├── gradient_boosting.py
│   ├── xgboost_model.py
│   └── lightgbm_model.py
├── training/
│   ├── train.py
│   ├── hyperparameter_tuning.py
│   ├── cross_validation.py
│   └── model_saver.py
├── evaluation/
│   ├── metrics.py
│   ├── model_comparison.py
│   ├── error_analysis.py
│   └── validation.py
├── explainability/
│   ├── feature_importance.py
│   ├── shap_explainer.py
│   └── prediction_explainer.py
├── inference/
│   ├── predictor.py
│   ├── batch_predictor.py
│   └── api_predictor.py
├── utils/
│   ├── config.py
│   ├── logger.py
│   └── helpers.py
└── notebooks/
    ├── eda.ipynb
    ├── feature_engineering.ipynb
    ├── model_training.ipynb
    └── evaluation.ipynb
```

**ML Pipeline Stages:**
1. **Data Collection**: Load raw datasets
2. **Data Validation**: Check data quality, schema validation
3. **Data Cleaning**: Remove duplicates, fix inconsistencies
4. **Missing Value Handling**: Impute or flag missing values
5. **Outlier Detection**: Identify anomalies using IQR, Z-score, Isolation Forest
6. **Feature Engineering**: Create domain-specific features
7. **Feature Selection**: Select most relevant features
8. **Train/Test Split**: Temporal or random split
9. **Baseline Model**: Reference calculation (ET0 × Kc)
10. **ML Models**: Train multiple regression models
11. **Hyperparameter Tuning**: Grid search, random search
12. **Cross Validation**: K-fold CV for robust evaluation
13. **Model Evaluation**: MAE, RMSE, R², MAPE
14. **Best Model Selection**: Based on validation metrics
15. **Explainability**: Feature importance, SHAP values
16. **Model Deployment**: Save model with metadata

---

## 3. Data Flow Architecture

### 3.1 Prediction Request Flow

```
Farmer Input (Flutter)
    ↓
Input Validation
    ↓
API Request (POST /prediction/cwr)
    ↓
FastAPI Endpoint
    ↓
PredictionService
    ↓
├── WeatherService → External Weather API
├── SoilService → PostgreSQL
├── CropService → PostgreSQL
└── GrowthStageService → PostgreSQL
    ↓
Feature Engineering (MLService)
    ↓
ML Model Inference
    ↓
CWR Prediction
    ↓
Irrigation Requirement Calculation
    ↓
Advisory Generation
    ↓
Prediction Explanation (Feature Importance)
    ↓
Response to Flutter
    ↓
Visualization & Display
```

### 3.2 Data Ingestion Flow

```
Raw Datasets (CSV/JSON/Excel)
    ↓
Dataset Loader
    ↓
Schema Validation
    ↓
Data Cleaning
    ↓
Missing Value Handling
    ↓
Outlier Detection & Flagging
    ↓
Feature Engineering
    ↓
Database Insertion (PostgreSQL)
    ↓
Data Quality Reports
```

---

## 4. Security Architecture

```
┌─────────────────────────────────────────┐
│         Security Layers                │
├─────────────────────────────────────────┤
│ 1. Network Layer                        │
│    - HTTPS/TLS 1.3                      │
│    - API Gateway                        │
│    - Rate Limiting                      │
├─────────────────────────────────────────┤
│ 2. Authentication Layer                 │
│    - JWT Tokens                         │
│    - Password Hashing (bcrypt)          │
│    - Token Refresh                      │
├─────────────────────────────────────────┤
│ 3. Authorization Layer                 │
│    - Role-Based Access Control          │
│    - API Endpoint Permissions          │
├─────────────────────────────────────────┤
│ 4. Application Layer                    │
│    - Input Validation                   │
│    - SQL Injection Prevention           │
│    - XSS Prevention                     │
├─────────────────────────────────────────┤
│ 5. Data Layer                           │
│    - Encrypted Database Connection      │
│    - Row-Level Security                 │
├─────────────────────────────────────────┤
│ 6. Secrets Management                   │
│    - Environment Variables              │
│    - Cloud Secret Manager               │
│    - No Hardcoded Secrets               │
└─────────────────────────────────────────┘
```

---

## 5. Research Architecture

```
┌─────────────────────────────────────────┐
│         Research Components             │
├─────────────────────────────────────────┤
│ Research Question:                      │
│ "How accurately can crop water          │
│  requirement be predicted using         │
│  crop, growth-stage, soil, weather      │
│  and rainfall information?"             │
├─────────────────────────────────────────┤
│ Baseline Approach:                      │
│ - ET0 Calculation (FAO Penman-Monteith) │
│ - Kc Values (Crop Coefficients)         │
│ - ETc = ET0 × Kc                        │
│ - Effective Rainfall (USDA SCS)         │
│ - Irrigation Requirement                │
├─────────────────────────────────────────┤
│ ML Approach:                            │
│ - Multiple Regression Models            │
│ - Feature Engineering                   │
│ - Hyperparameter Tuning                 │
│ - Cross Validation                      │
├─────────────────────────────────────────┤
│ Comparison:                             │
│ - MAE, RMSE, R², MAPE                   │
│ - Model Comparison                      │
│ - Feature Importance                     │
│ - Error Analysis                        │
├─────────────────────────────────────────┤
│ Explainability:                         │
│ - Feature Importance                    │
│ - SHAP Values                           │
│ - Prediction Explanation                │
└─────────────────────────────────────────┘
```

---

## 6. Technology Stack Summary

### Frontend
- **Framework**: Flutter 3.x
- **Language**: Dart
- **State Management**: Provider/Riverpod
- **Charts**: FL Chart / Chart.js (Web)
- **HTTP**: Dio
- **Local Storage**: Hive/SharedPreferences

### Backend
- **Framework**: FastAPI 0.104+
- **Language**: Python 3.11+
- **ORM**: SQLAlchemy 2.0
- **Database**: PostgreSQL 15+
- **Authentication**: JWT (python-jose)
- **Validation**: Pydantic v2

### ML/Data Science
- **Core**: scikit-learn, pandas, numpy
- **Models**: XGBoost, LightGBM
- **Explainability**: SHAP
- **Visualization**: matplotlib, seaborn
- **Notebooks**: Jupyter

### DevOps/Cloud
- **Containerization**: Docker, Docker Compose
- **CI/CD**: GitHub Actions
- **Cloud Provider**: AWS/GCP/Azure (configurable)
- **Object Storage**: S3/GCS/Azure Blob
- **Secret Management**: Environment Variables / Cloud Secrets

### Weather API
- **Primary**: OpenWeatherMap / WeatherAPI
- **Architecture**: Service abstraction for easy switching

---

## 7. Key Design Decisions

### 7.1 Why Flutter?
- Cross-platform (Android + Web)
- Modern UI components
- Good performance
- Large ecosystem

### 7.2 Why FastAPI?
- Async support for high performance
- Automatic API documentation
- Type hints with Pydantic
- Modern Python framework

### 7.3 Why PostgreSQL?
- Relational data model fits the domain
- ACID compliance
- JSON support for flexible data
- Strong ecosystem

### 7.4 Why Separate ML Service?
- Clear separation of concerns
- Independent model updates
- Easier testing and validation
- Research reproducibility

### 7.5 Why Service Abstraction for Weather?
- API provider changes
- Rate limit handling
- Fallback mechanisms
- Cost optimization

---

## 8. Scalability Considerations

### Horizontal Scaling
- Stateless FastAPI instances
- Load balancer distribution
- Database connection pooling
- Caching layer (Redis) for weather data

### Vertical Scaling
- ML model optimization
- Database indexing
- Query optimization
- Efficient feature engineering

### Data Volume
- Partitioned tables by date/location
- Archival of old predictions
- Efficient data retention policies

---

## 9. Monitoring & Observability

### Application Monitoring
- API response times
- Error rates
- Prediction latency
- Weather API call frequency

### Data Quality Monitoring
- Missing value rates
- Anomaly detection rates
- Data freshness checks
- Schema validation alerts

### Model Monitoring
- Prediction distribution drift
- Feature distribution drift
- Model performance over time
- Prediction confidence scores

---

## 10. Disaster Recovery

### Database Backups
- Daily automated backups
- Point-in-time recovery
- Cross-region replication

### Model Versioning
- All model versions saved
- Rollback capability
- Model metadata tracking

### Code Repository
- Git version control
- Branch protection
- Code review process
