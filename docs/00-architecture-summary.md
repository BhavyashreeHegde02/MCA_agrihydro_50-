# Architecture & Implementation Plan Summary
## Smart Crop Water Requirement Prediction System

---

## Executive Summary

This document provides a comprehensive summary of the complete architecture and implementation plan for the **Smart Crop Water Requirement Prediction and Farmer Advisory System**. The system is a research-oriented agricultural decision-support platform focused on predicting Crop Water Requirement (CWR) using machine learning, weather data, soil information, and crop growth stages.

---

## A. What Will Be Implemented First

### Phase 1: Project Setup (Week 1-2)

**Immediate Implementation Order**:

1. **Repository Initialization**
   - Create Git repository with `.gitignore`
   - Set up monorepo structure
   - Configure branch protection rules

2. **Folder Structure Creation**
   - Create `/frontend`, `/backend`, `/ml`, `/datasets` directories
   - Create subdirectories as per architecture
   - Create placeholder files

3. **Development Environment Setup**
   - Configure Docker Compose for local development
   - Set up PostgreSQL and Redis containers
   - Configure Python virtual environment for backend
   - Configure Flutter SDK for frontend
   - Configure Jupyter for ML development

4. **Documentation Structure**
   - Create all architecture documents (completed)
   - Create README.md
   - Create .env.example file

**First Working Deliverable**: Local development environment with Docker Compose running PostgreSQL, Redis, and basic backend structure.

---

## B. Which Files Will Be Created

### Root Level Files
```
smart-crop-water-requirement-system/
├── README.md
├── .gitignore
├── .env.example
├── docker-compose.yml
├── LICENSE
└── docker-compose.prod.yml
```

### Backend Files (Key Files)
```
backend/
├── app/
│   ├── main.py                          # FastAPI application entry point
│   ├── config/
│   │   ├── settings.py                  # Configuration settings
│   │   ├── logging.py                   # Logging configuration
│   │   └── constants.py                 # Application constants
│   ├── api/
│   │   ├── deps.py                      # Dependencies
│   │   └── v1/
│   │       ├── api.py                   # API router
│   │       └── endpoints/
│   │           ├── auth.py              # Authentication endpoints
│   │           ├── farms.py             # Farm management endpoints
│   │           ├── crops.py             # Crop endpoints
│   │           ├── soil.py              # Soil endpoints
│   │           ├── weather.py           # Weather endpoints
│   │           ├── predictions.py       # CWR prediction endpoints
│   │           ├── irrigation.py        # Irrigation endpoints
│   │           ├── water_use.py         # Water use endpoints
│   │           ├── analytics.py         # Analytics endpoints
│   │           ├── advisory.py          # Advisory endpoints
│   │           ├── data_quality.py      # Data quality endpoints
│   │           └── admin.py             # Admin endpoints
│   ├── models/
│   │   ├── user.py                      # User model
│   │   ├── farmer.py                    # Farmer model
│   │   ├── farm.py                      # Farm model
│   │   ├── field.py                     # Field model
│   │   ├── crop.py                      # Crop model
│   │   ├── crop_growth_stage.py         # Growth stage model
│   │   ├── soil.py                      # Soil model
│   │   ├── weather.py                   # Weather model
│   │   ├── prediction.py                # Prediction model
│   │   └── irrigation.py                # Irrigation model
│   ├── schemas/
│   │   ├── user.py                      # User schemas
│   │   ├── farmer.py                    # Farmer schemas
│   │   ├── farm.py                      # Farm schemas
│   │   ├── crop.py                      # Crop schemas
│   │   ├── soil.py                      # Soil schemas
│   │   ├── weather.py                   # Weather schemas
│   │   └── prediction.py                # Prediction schemas
│   ├── services/
│   │   ├── auth_service.py              # Authentication service
│   │   ├── farm_service.py              # Farm service
│   │   ├── crop_service.py              # Crop service
│   │   ├── soil_service.py              # Soil service
│   │   ├── weather_service.py           # Weather service
│   │   ├── prediction_service.py       # Prediction service
│   │   ├── irrigation_service.py        # Irrigation service
│   │   ├── advisory_service.py          # Advisory service
│   │   ├── anomaly_service.py           # Anomaly detection service
│   │   └── ml_service.py                # ML inference service
│   ├── database/
│   │   ├── connection.py                # Database connection
│   │   ├── base.py                      # Base model
│   │   └── repositories/               # Data access layer
│   └── ml/
│       ├── inference.py                 # ML inference
│       ├── feature_engineering.py       # Feature engineering
│       ├── model_loader.py              # Model loading
│       └── predictor.py                 # Prediction logic
├── tests/
│   ├── unit/                           # Unit tests
│   ├── integration/                    # Integration tests
│   └── fixtures/                       # Test fixtures
├── alembic/
│   ├── versions/                       # Database migrations
│   ├── env.py                          # Alembic environment
│   └── alembic.ini                     # Alembic configuration
├── requirements.txt                     # Production dependencies
├── requirements-dev.txt                 # Development dependencies
├── Dockerfile                          # Backend Dockerfile
└── pyproject.toml                      # Python project configuration
```

### Frontend Files (Key Files)
```
frontend/
├── lib/
│   ├── main.dart                        # Flutter entry point
│   ├── app.dart                         # App widget
│   ├── config/
│   │   ├── api_config.dart              # API configuration
│   │   ├── app_config.dart              # App configuration
│   │   ├── theme_config.dart            # Theme configuration
│   │   └── routes_config.dart           # Routes configuration
│   ├── core/
│   │   ├── constants/                   # App constants
│   │   ├── utils/                       # Utility functions
│   │   ├── validators/                  # Form validators
│   │   ├── exceptions/                  # Custom exceptions
│   │   └── theme/                       # Theme configuration
│   ├── data/
│   │   ├── models/                      # Data models
│   │   ├── repositories/                # Data repositories
│   │   └── services/                    # API services
│   ├── domain/
│   │   ├── entities/                    # Domain entities
│   │   └── usecases/                    # Business logic
│   ├── presentation/
│   │   ├── pages/                       # UI pages
│   │   ├── widgets/                     # Reusable widgets
│   │   ├── providers/                   # State management
│   │   └── screens/                     # Screen-specific widgets
│   └── routes/                          # Navigation routes
├── android/                             # Android configuration
├── ios/                                 # iOS configuration
├── web/                                 # Web configuration
├── pubspec.yaml                         # Flutter dependencies
├── analysis_options.yaml                # Dart linting rules
└── Dockerfile                           # Frontend Dockerfile (web)
```

### ML Pipeline Files (Key Files)
```
ml/
├── data/
│   ├── raw/                             # Raw datasets
│   ├── processed/                       # Processed datasets
│   ├── features/                        # Engineered features
│   └── splits/                          # Train/val/test splits
├── preprocessing/
│   ├── data_loader.py                   # Data loading
│   ├── data_cleaner.py                  # Data cleaning
│   ├── missing_value_handler.py         # Missing value handling
│   ├── outlier_detector.py              # Outlier detection
│   └── data_validator.py                # Data validation
├── feature_engineering/
│   ├── weather_features.py              # Weather feature engineering
│   ├── soil_features.py                 # Soil feature engineering
│   ├── crop_features.py                 # Crop feature engineering
│   ├── temporal_features.py             # Temporal feature engineering
│   ├── rainfall_features.py             # Rainfall feature engineering
│   ├── feature_selector.py             # Feature selection
│   └── feature_scaler.py                # Feature scaling
├── models/
│   ├── base_model.py                    # Base model class
│   ├── baseline.py                      # Baseline model (ET0 × Kc)
│   ├── linear_regression.py             # Linear Regression
│   ├── random_forest.py                 # Random Forest
│   ├── gradient_boosting.py             # Gradient Boosting
│   ├── xgboost_model.py                 # XGBoost (optional)
│   └── lightgbm_model.py                # LightGBM (optional)
├── training/
│   ├── train.py                         # Training script
│   ├── hyperparameter_tuning.py         # Hyperparameter tuning
│   ├── cross_validation.py              # Cross validation
│   └── model_saver.py                   # Model saving
├── evaluation/
│   ├── metrics.py                       # Evaluation metrics
│   ├── model_comparison.py              # Model comparison
│   ├── error_analysis.py                # Error analysis
│   └── validation.py                    # Validation logic
├── explainability/
│   ├── feature_importance.py            # Feature importance
│   ├── shap_explainer.py                # SHAP explainer
│   └── prediction_explainer.py         # Prediction explanation
├── inference/
│   ├── predictor.py                     # Prediction class
│   ├── batch_predictor.py               # Batch prediction
│   └── api_predictor.py                 # API prediction
├── utils/
│   ├── config.py                        # ML configuration
│   ├── logger.py                        # Logging
│   └── helpers.py                       # Helper functions
├── notebooks/
│   ├── 01_eda.ipynb                     # Exploratory data analysis
│   ├── 02_feature_engineering.ipynb     # Feature engineering
│   ├── 03_model_training.ipynb          # Model training
│   ├── 04_model_evaluation.ipynb        # Model evaluation
│   └── 05_explainability.ipynb          # Explainability
├── saved_models/
│   ├── baseline_model.pkl               # Baseline model
│   ├── best_model.pkl                   # Best ML model
│   ├── feature_scaler.pkl               # Feature scaler
│   └── model_metadata.json              # Model metadata
├── requirements.txt                     # ML dependencies
└── README.md                            # ML documentation
```

### Dataset Files
```
datasets/
├── crop/
│   ├── crop_catalog.csv                 # Crop catalog
│   ├── crop_varieties.csv              # Crop varieties
│   └── crop_kc_values.csv              # Crop Kc values
├── soil/
│   ├── soil_types.csv                   # Soil types
│   ├── soil_parameters.csv              # Soil parameters
│   └── district_soil_mapping.csv        # District soil mapping
├── weather/
│   ├── historical_weather.csv           # Historical weather
│   └── weather_stations.csv             # Weather stations
├── rainfall/
│   ├── historical_rainfall.csv         # Historical rainfall
│   └── district_rainfall.csv           # District rainfall
├── growth_stage/
│   ├── crop_growth_stages.csv           # Crop growth stages
│   └── stage_kc_values.csv              # Stage Kc values
└── reference/
    ├── et0_reference.csv                # ET0 reference data
    ├── irrigation_efficiency.csv       # Irrigation efficiency
    └── crop_water_requirement_reference.csv  # CWR reference
```

### DevOps Files
```
.github/
└── workflows/
    ├── ci.yml                          # Continuous Integration
    ├── cd.yml                          # Continuous Deployment
    └── test.yml                        # Testing workflow

docker/
├── frontend.Dockerfile                 # Frontend Dockerfile
├── backend.Dockerfile                  # Backend Dockerfile
├── ml.Dockerfile                       # ML Dockerfile
├── nginx.conf                          # Nginx configuration
└── docker-compose.prod.yml             # Production Docker Compose

k8s/
├── namespaces.yaml                     # Kubernetes namespaces
├── configmap.yaml                      # ConfigMaps
├── secrets.yaml                        # Secrets (example)
├── backend-deployment.yaml             # Backend deployment
├── postgres-deployment.yaml            # PostgreSQL deployment
├── redis-deployment.yaml               # Redis deployment
└── prometheus-config.yaml              # Prometheus configuration
```

---

## C. Which Datasets Are Required

### Essential Datasets (Required)

1. **Crop Catalog Dataset**
   - **File**: `datasets/crop/crop_catalog.csv`
   - **Fields**: crop_id, name, scientific_name, category, growing_season, duration_days
   - **Purpose**: Crop information and characteristics
   - **Source**: Agricultural research institutions, government databases

2. **Crop Growth Stage Dataset**
   - **File**: `datasets/growth_stage/crop_growth_stages.csv`
   - **Fields**: stage_id, crop_id, stage_name, stage_order, duration_days, kc_value
   - **Purpose**: Growth stage information with Kc values
   - **Source**: FAO-56, ICAR, agricultural research

3. **Soil Parameters Dataset**
   - **File**: `datasets/soil/soil_parameters.csv`
   - **Fields**: soil_id, state, district, dominant_soil_type, ph_avg, nitrogen_avg, phosphorus_avg, potassium_avg
   - **Purpose**: Soil information by district
   - **Source**: Soil surveys, agricultural departments

4. **Historical Weather Dataset**
   - **File**: `datasets/weather/historical_weather.csv`
   - **Fields**: weather_id, district, date, temperature_max, temperature_min, temperature_avg, humidity, wind_speed, rainfall, solar_radiation
   - **Purpose**: Historical weather data for ML training
   - **Source**: IMD (India Meteorological Department), NOAA, weather APIs

5. **Historical Rainfall Dataset**
   - **File**: `datasets/rainfall/historical_rainfall.csv`
   - **Fields**: rainfall_id, district, date, daily_rainfall, weekly_rainfall, monthly_rainfall
   - **Purpose**: Historical rainfall data for ML training
   - **Source**: IMD, rainfall monitoring stations

### Optional Datasets (Enhance System)

6. **Crop Varieties Dataset**
   - **File**: `datasets/crop/crop_varieties.csv`
   - **Purpose**: Crop variety information
   - **Source**: Agricultural research institutes

7. **ET0 Reference Dataset**
   - **File**: `datasets/reference/et0_reference.csv`
   - **Purpose**: Reference evapotranspiration data
   - **Source**: FAO, meteorological data

8. **Irrigation Efficiency Dataset**
   - **File**: `datasets/reference/irrigation_efficiency.csv`
   - **Purpose**: Irrigation method efficiency values
   - **Source**: Agricultural engineering research

### Dataset Requirements Summary

| Dataset | Required | Records Needed | Time Period | Source |
|---------|----------|---------------|-------------|--------|
| Crop Catalog | Yes | 50-100 | N/A | Agricultural databases |
| Growth Stages | Yes | 200-300 | N/A | FAO-56, ICAR |
| Soil Parameters | Yes | 500-1000 | N/A | Soil surveys |
| Historical Weather | Yes | 10,000+ | 3-5 years | IMD, NOAA |
| Historical Rainfall | Yes | 10,000+ | 3-5 years | IMD |
| Crop Varieties | No | 100-200 | N/A | Research institutes |
| ET0 Reference | No | 5,000+ | 3-5 years | Calculated/FAO |
| Irrigation Efficiency | No | 10-20 | N/A | Research |

---

## D. Which Fields Are Required

### Farmer Input Fields (Required)

**Location**:
- State (dropdown)
- District (dropdown - state-dependent)
- Tanuk (optional)
- Latitude (auto-fill from map)
- Longitude (auto-fill from map)

**Farm**:
- Farm Name (text)
- Total Area (number)
- Area Unit (dropdown: acres, hectares)

**Field**:
- Field Name (text)
- Area (number)
- Soil Type (dropdown)
- Irrigation Method (dropdown)
- Irrigation Efficiency (number, optional)

**Crop**:
- Crop (dropdown)
- Crop Variety (dropdown - optional)
- Sowing Date (date picker)
- Current Growth Stage (dropdown - auto-calculated)

**Soil** (optional - can auto-fill from district):
- pH Level (number, 0-14)
- Nitrogen (number, kg/ha)
- Phosphorus (number, kg/ha)
- Potassium (number, kg/ha)
- Soil Moisture (number, %)
- Electrical Conductivity (number, dS/m)

**Weather** (auto-retrieved from API):
- Temperature (auto)
- Humidity (auto)
- Wind Speed (auto)
- Rainfall (auto)
- Solar Radiation (auto if available)

### Database Fields (Key Tables)

**Users Table**:
- id, email, password_hash, full_name, phone, is_active, created_at, updated_at

**Farmers Table**:
- id, user_id, full_name, phone, state, district, taluk, address, created_at, updated_at

**Farms Table**:
- id, farmer_id, name, state, district, taluk, latitude, longitude, total_area, area_unit, created_at, updated_at

**Fields Table**:
- id, farm_id, name, area, area_unit, soil_type, irrigation_method, irrigation_efficiency, created_at, updated_at

**Crops Table**:
- id, name, scientific_name, category, growing_season, duration_days, created_at

**Crop Growth Stages Table**:
- id, crop_id, stage_name, stage_order, duration_days, kc_value, description, created_at

**Field Crops Table**:
- id, field_id, crop_id, variety_id, sowing_date, current_stage_id, planting_area, status, created_at, updated_at

**Soil Data Table**:
- id, field_id, sample_date, ph_level, nitrogen, phosphorus, potassium, soil_moisture, electrical_conductivity, organic_matter, texture, created_at

**Weather Data Table**:
- id, district, date, temperature_max, temperature_min, temperature_avg, humidity, wind_speed, rainfall, solar_radiation, et0, data_source, created_at

**Predictions Table**:
- id, field_crop_id, prediction_date, model_version_id, cwr_mm_day, cwr_mm_week, effective_rainfall, irrigation_requirement, weather_data (JSONB), soil_data (JSONB), features (JSONB), prediction_confidence, created_at

---

## E. Which ML Target Is Used

### Primary Target Variable

**Crop Water Requirement (CWR)** - Measured in mm/day

**Target Definition**:
- **Variable**: `cwr_mm_day` (Crop Water Requirement in mm per day)
- **Type**: Continuous regression target
- **Range**: Typically 2-10 mm/day for most crops
- **Unit**: mm/day (millimeters per day)

### Secondary Targets (Derived)

1. **Weekly CWR** (`cwr_mm_week`): CWR × 7 days
2. **Effective Rainfall** (`effective_rainfall`): Calculated using USDA SCS method
3. **Irrigation Requirement** (`irrigation_requirement`): CWR - Effective Rainfall

### Target Calculation

**Baseline Method (Reference)**:
```
ETc = ET0 × Kc
CWR = ETc
```

Where:
- ET0 = Reference evapotranspiration (FAO Penman-Monteith)
- Kc = Crop coefficient (from growth stage)
- ETc = Crop evapotranspiration

**ML Method**:
- Direct prediction of CWR using engineered features
- Features: temperature, humidity, rainfall, soil parameters, crop type, growth stage, Kc value, etc.

### Target Data Sources

**For Training**:
- Historical CWR reference data (if available)
- Calculated CWR from baseline method (ET0 × Kc)
- Field measurements (if available from research stations)

**For Inference**:
- Predicted by ML model
- Used to calculate irrigation requirement

---

## F. How CWR Is Calculated/Predicted

### Calculation/Prediction Flow

```
Input Data Collection
    ↓
┌─────────────────────────────────────┐
│  1. Crop Information               │
│     - Crop type                     │
│     - Growth stage                 │
│     - Kc value                     │
│     - Days after sowing            │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  2. Weather Data                   │
│     - Temperature (max, min, avg)  │
│     - Humidity                     │
│     - Wind speed                   │
│     - Rainfall                     │
│     - Solar radiation              │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  3. Soil Data                      │
│     - pH level                     │
│     - Nitrogen                     │
│     - Phosphorus                   │
│     - Potassium                    │
│     - Soil moisture                │
│     - Soil type                    │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  4. Feature Engineering            │
│     - Weather features             │
│     - Soil features                │
│     - Crop features                │
│     - Temporal features            │
│     - Rainfall features            │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  5. ML Model Prediction           │
│     - Load trained model           │
│     - Preprocess features          │
│     - Predict CWR (mm/day)        │
│     - Return prediction            │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  6. Irrigation Requirement         │
│     - Calculate effective rainfall │
│     - Irrigation = CWR - Eff. Rain │
│     - Apply irrigation efficiency  │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  7. Advisory Generation           │
│     - Analyze prediction          │
│     - Generate farmer advisory     │
│     - Provide explanation          │
└─────────────────────────────────────┘
```

### Baseline Calculation (Reference)

**Step 1: Calculate ET0 (Reference Evapotranspiration)**
```
Using FAO Penman-Monteith equation:
ET0 = (0.408 × Δ × (Rn - G) + γ × (900/(T + 273)) × u2 × (es - ea)) / (Δ + γ × (1 + 0.34 × u2))

Where:
- Rn = Net radiation
- G = Soil heat flux
- T = Air temperature
- u2 = Wind speed at 2m height
- es = Saturation vapor pressure
- ea = Actual vapor pressure
- Δ = Slope of vapor pressure curve
- γ = Psychrometric constant
```

**Step 2: Calculate ETc (Crop Evapotranspiration)**
```
ETc = ET0 × Kc

Where:
- Kc = Crop coefficient (from growth stage)
```

**Step 3: Calculate Effective Rainfall**
```
Using USDA SCS method:
P_eff = 0.8 × P (if P ≤ 250mm)
P_eff = 125 + 0.5 × (P - 250) (if P > 250mm)

Where:
- P = Total rainfall
- P_eff = Effective rainfall
```

**Step 4: Calculate Irrigation Requirement**
```
IR = ETc - P_eff

Where:
- IR = Irrigation requirement
- If IR < 0, IR = 0
```

### ML Prediction Method

**Step 1: Feature Engineering**
```python
features = {
    # Weather features
    'temperature_avg': weather['temperature_avg'],
    'humidity': weather['humidity'],
    'wind_speed': weather['wind_speed'],
    'rainfall': weather['rainfall'],
    
    # Soil features
    'soil_ph': soil['ph_level'],
    'nitrogen': soil['nitrogen'],
    'phosphorus': soil['phosphorus'],
    'potassium': soil['potassium'],
    
    # Crop features
    'kc_value': growth_stage['kc_value'],
    'days_after_sowing': (current_date - sowing_date).days,
    'growth_stage_order': growth_stage['stage_order'],
    
    # Temporal features
    'month': current_date.month,
    'season': get_season(current_date.month),
    
    # Engineered features
    'temp_range': weather['temperature_max'] - weather['temperature_min'],
    'np_ratio': soil['nitrogen'] / (soil['phosphorus'] + 1e-6),
}
```

**Step 2: Model Prediction**
```python
# Load trained model
model = joblib.load('ml/saved_models/best_model.pkl')

# Load feature scaler
scaler = joblib.load('ml/saved_models/feature_scaler.pkl')

# Scale features
features_scaled = scaler.transform([features])

# Predict
cwr_mm_day = model.predict(features_scaled)[0]
```

**Step 3: Calculate Derived Values**
```python
cwr_mm_week = cwr_mm_day * 7
effective_rainfall = calculate_effective_rainfall(weather['rainfall'])
irrigation_requirement = max(0, cwr_mm_week - effective_rainfall)
```

### Model Comparison

| Method | Description | Advantages | Disadvantages |
|--------|-------------|------------|---------------|
| Baseline (ET0 × Kc) | Scientific calculation | Interpretable, scientifically valid | May not capture local variations |
| Linear Regression | Simple ML model | Fast, interpretable | May underfit complex relationships |
| Random Forest | Ensemble method | Handles non-linearities, feature importance | Slower inference |
| Gradient Boosting | Sequential ensemble | High accuracy | More complex, less interpretable |
| XGBoost/LightGBM | Optimized boosting | Very high accuracy, fast | Requires more tuning |

---

## G. How Flutter Application Communicates with Backend

### Communication Architecture

```
Flutter App
    │
    │ HTTP/HTTPS (REST API)
    │ JSON Request/Response
    │ JWT Authentication
    ↓
FastAPI Backend
    │
    │ Business Logic
    │
    ↓
PostgreSQL Database
```

### API Communication Flow

**1. Authentication Flow**
```dart
// Flutter (Login)
final response = await dio.post(
  '/api/v1/auth/login',
  data: {
    'email': email,
    'password': password,
  },
);

// Store JWT token
final token = response.data['access_token'];
await storageService.saveToken(token);
```

**2. Authenticated Request Flow**
```dart
// Flutter API Service
class APIService {
  final Dio _dio = Dio(BaseOptions(
    baseUrl: 'https://api.cropwater-prediction.com/api/v1',
  ));

  Future<Prediction> predictCWR(PredictionRequest request) async {
    final token = await storageService.getToken();
    
    final response = await _dio.post(
      '/predictions/cwr',
      data: request.toJson(),
      options: Options(
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/json',
        },
      ),
    );
    
    return Prediction.fromJson(response.data);
  }
}
```

**3. Backend Request Handling**
```python
# FastAPI Endpoint
@router.post("/predictions/cwr")
async def predict_cwr(
    request: PredictionRequest,
    current_user: User = Depends(get_current_user),
):
    # Business logic
    prediction = await prediction_service.predict_cwr(
        field_crop_id=request.field_crop_id,
        prediction_date=request.prediction_date,
    )
    
    return prediction
```

### Data Models (Flutter ↔ Backend)

**Example: Prediction Model**

**Backend (Pydantic Schema)**:
```python
class PredictionResponse(BaseModel):
    id: int
    field_crop_id: int
    prediction_date: date
    crop: CropInfo
    growth_stage: GrowthStageInfo
    cwr_mm_day: Decimal
    cwr_mm_week: Decimal
    effective_rainfall: Decimal
    irrigation_requirement: Decimal
    weather_data: dict
    soil_data: dict
    prediction_confidence: float
    model_version: str
```

**Flutter (Dart Model)**:
```dart
class Prediction {
  final int id;
  final int fieldCropId;
  final DateTime predictionDate;
  final CropInfo crop;
  final GrowthStageInfo growthStage;
  final double cwrMmDay;
  final double cwrMmWeek;
  final double effectiveRainfall;
  final double irrigationRequirement;
  final Map<String, dynamic> weatherData;
  final Map<String, dynamic> soilData;
  final double predictionConfidence;
  final String modelVersion;

  factory Prediction.fromJson(Map<String, dynamic> json) {
    return Prediction(
      id: json['id'],
      fieldCropId: json['field_crop_id'],
      predictionDate: DateTime.parse(json['prediction_date']),
      crop: CropInfo.fromJson(json['crop']),
      growthStage: GrowthStageInfo.fromJson(json['growth_stage']),
      cwrMmDay: json['cwr_mm_day'].toDouble(),
      cwrMmWeek: json['cwr_mm_week'].toDouble(),
      effectiveRainfall: json['effective_rainfall'].toDouble(),
      irrigationRequirement: json['irrigation_requirement'].toDouble(),
      weatherData: json['weather_data'],
      soilData: json['soil_data'],
      predictionConfidence: json['prediction_confidence'].toDouble(),
      modelVersion: json['model_version'],
    );
  }
}
```

### State Management Integration

**Provider Pattern**:
```dart
class PredictionProvider with ChangeNotifier {
  final APIService _apiService;
  Prediction? _currentPrediction;
  bool _isLoading = false;

  PredictionProvider(this._apiService);

  Prediction? get currentPrediction => _currentPrediction;
  bool get isLoading => _isLoading;

  Future<void> predictCWR(PredictionRequest request) async {
    _isLoading = true;
    notifyListeners();

    try {
      _currentPrediction = await _apiService.predictCWR(request);
    } catch (e) {
      // Handle error
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }
}
```

### Error Handling

**Flutter Side**:
```dart
try {
  final prediction = await predictionProvider.predictCWR(request);
} on DioException catch (e) {
  if (e.response?.statusCode == 401) {
    // Unauthorized - redirect to login
    Navigator.pushReplacementNamed(context, '/login');
  } else if (e.response?.statusCode == 500) {
    // Server error - show error message
    showErrorDialog('Server error. Please try again.');
  }
} catch (e) {
  // Other errors
  showErrorDialog('An error occurred.');
}
```

**Backend Side**:
```python
@app.exception_handler(AuthException)
async def auth_exception_handler(request: Request, exc: AuthException):
    return JSONResponse(
        status_code=401,
        content={"error": "UNAUTHORIZED", "message": str(exc)}
    )

@app.exception_handler(ValidationException)
async def validation_exception_handler(request: Request, exc: ValidationException):
    return JSONResponse(
        status_code=400,
        content={"error": "VALIDATION_ERROR", "message": str(exc)}
    )
```

---

## H. How Cloud Deployment Will Work

### Deployment Architecture

```
Developer
    │
    │ Git Push
    ↓
GitHub Repository
    │
    │ Trigger CI/CD
    ↓
GitHub Actions (CI)
    │
    ├─→ Build Docker Images
    ├─→ Run Tests
    ├─→ Security Scan
    └─→ Push to Container Registry
    │
    ↓
GitHub Actions (CD)
    │
    ├─→ Deploy to Staging (on PR merge)
    │   │
    │   ├─→ Update Kubernetes Deployment
    │   ├─→ Run Database Migrations
    │   └─→ Health Checks
    │
    └─→ Deploy to Production (on tag)
        │
        ├─→ Blue-Green Deployment
        ├─→ Database Migrations
        ├─→ Health Checks
        └─→ Rollback on Failure
```

### Deployment Steps

**1. Containerization**
```dockerfile
# Backend Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**2. Kubernetes Deployment**
```yaml
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
        image: ghcr.io/your-repo/backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: backend-secrets
              key: database-url
```

**3. CI/CD Pipeline**
```yaml
# GitHub Actions
name: Deploy to Production

on:
  push:
    tags:
      - 'v*'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Configure kubectl
        uses: azure/k8s-set-context@v3
        with:
          method: kubeconfig
          kubeconfig: ${{ secrets.PRODUCTION_KUBECONFIG }}
      
      - name: Deploy to Kubernetes
        run: |
          kubectl set image deployment/backend-deployment \
            backend=ghcr.io/your-repo/backend:${{ github.ref_name }} \
            -n production
          
          kubectl rollout status deployment/backend-deployment -n production
```

**4. Cloud Infrastructure Setup**

**AWS Example**:
- **EKS**: Kubernetes cluster
- **RDS**: PostgreSQL database
- **ElastiCache**: Redis cache
- **S3**: Object storage for datasets/models
- **CloudFront**: CDN for Flutter web build
- **Route 53**: DNS management
- **Secrets Manager**: Secret management

**GCP Example**:
- **GKE**: Kubernetes cluster
- **Cloud SQL**: PostgreSQL database
- **Memorystore**: Redis cache
- **Cloud Storage**: Object storage
- **Cloud CDN**: CDN
- **Cloud DNS**: DNS management
- **Secret Manager**: Secret management

**Azure Example**:
- **AKS**: Kubernetes cluster
- **Azure Database for PostgreSQL**: Database
- **Azure Cache for Redis**: Redis cache
- **Blob Storage**: Object storage
- **Azure CDN**: CDN
- **Azure DNS**: DNS management
- **Key Vault**: Secret management

### Environment Configuration

**Development**:
- Local Docker Compose
- Local PostgreSQL
- Mock weather API
- No auto-scaling

**Staging**:
- Small Kubernetes cluster
- Managed PostgreSQL (dev tier)
- Real weather API (test key)
- Basic auto-scaling

**Production**:
- Full Kubernetes cluster
- Managed PostgreSQL (production tier)
- Real weather API (production key)
- Full auto-scaling
- Disaster recovery enabled

### Monitoring & Scaling

**Auto-scaling**:
```yaml
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
```

**Monitoring**:
- Prometheus for metrics collection
- Grafana for visualization
- CloudWatch/Cloud Monitoring for logs
- PagerDuty/Slack for alerts

---

## Summary of Key Decisions

### Technology Stack
- **Frontend**: Flutter (Android + Web)
- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL
- **ML**: scikit-learn, XGBoost/LightGBM
- **Cache**: Redis
- **Container**: Docker
- **Orchestration**: Kubernetes
- **CI/CD**: GitHub Actions
- **Cloud**: AWS/GCP/Azure (configurable)

### Architecture Patterns
- **Frontend**: Clean Architecture with Provider state management
- **Backend**: Layered architecture (API → Service → Repository → Database)
- **ML**: Separate pipeline with independent model training
- **Deployment**: Microservices with Kubernetes orchestration

### Research Focus
- **Primary**: Crop Water Requirement Prediction
- **Approach**: Compare baseline (ET0 × Kc) vs ML models
- **Models**: Linear Regression, Random Forest, Gradient Boosting
- **Evaluation**: MAE, RMSE, R², MAPE
- **Explainability**: Feature importance, SHAP values

### Key Features
1. Farmer registration and authentication
2. Farm and field management
3. Crop and growth stage selection
4. Soil information management
5. Weather data integration
6. CWR prediction using ML
7. Irrigation requirement calculation
8. Farmer advisory generation
9. Water use tracking
10. Historical CWR analysis
11. Data quality anomaly detection
12. Admin/research dashboard

---

## Next Steps

### Immediate Actions (Upon Approval)

1. **Initialize Repository**
   - Create Git repository
   - Set up folder structure
   - Configure development environment

2. **Set Up Database**
   - Install PostgreSQL
   - Create database schema
   - Set up Alembic migrations

3. **Acquire Datasets**
   - Source crop catalog data
   - Source soil parameter data
   - Source historical weather data
   - Source historical rainfall data

4. **Begin Backend Development**
   - Set up FastAPI application
   - Implement authentication
   - Create CRUD endpoints

5. **Begin ML Pipeline**
   - Perform exploratory data analysis
   - Implement data preprocessing
   - Train baseline model

### First Milestone (Week 4)
- Database schema complete
- Datasets loaded
- Basic backend structure
- Baseline model implemented

### Second Milestone (Week 8)
- All API endpoints complete
- ML models trained and evaluated
- Best model selected
- Ready for frontend integration

### Third Milestone (Week 13)
- Flutter application complete
- All screens implemented
- API integration complete
- System fully integrated

### Final Milestone (Week 20)
- System deployed to production
- Monitoring configured
- Documentation complete
- Research report complete
- Ready for project submission

---

## Conclusion

This architecture and implementation plan provides a comprehensive roadmap for building a research-oriented agricultural decision-support system focused on Crop Water Requirement Prediction. The system combines modern technologies (Flutter, FastAPI, ML, Kubernetes) with scientific agricultural principles (FAO Penman-Monteith, Kc values) to create a practical tool for farmers while maintaining academic rigor for research evaluation.

The phased approach ensures systematic development with clear milestones, while the modular architecture allows for flexibility and scalability. The separation of concerns between frontend, backend, and ML pipeline ensures maintainability and research reproducibility.
