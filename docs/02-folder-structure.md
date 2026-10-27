# Project Folder Structure
## Smart Crop Water Requirement Prediction System

---

## Complete Monorepo Structure

```
smart-crop-water-requirement-system/
│
├── README.md
├── .gitignore
├── .env.example
├── docker-compose.yml
├── LICENSE
│
├── frontend/                          # Flutter Application
│   ├── lib/
│   │   ├── main.dart
│   │   ├── app.dart
│   │   │
│   │   ├── config/
│   │   │   ├── api_config.dart
│   │   │   ├── app_config.dart
│   │   │   ├── theme_config.dart
│   │   │   └── routes_config.dart
│   │   │
│   │   ├── core/
│   │   │   ├── constants/
│   │   │   │   ├── app_constants.dart
│   │   │   │   ├── api_constants.dart
│   │   │   │   └── storage_constants.dart
│   │   │   ├── utils/
│   │   │   │   ├── date_utils.dart
│   │   │   │   ├── validators.dart
│   │   │   │   └── formatters.dart
│   │   │   ├── exceptions/
│   │   │   │   ├── app_exceptions.dart
│   │   │   │   └── api_exceptions.dart
│   │   │   └── theme/
│   │   │       ├── app_colors.dart
│   │   │       ├── app_text_styles.dart
│   │   │       └── app_theme.dart
│   │   │
│   │   ├── data/
│   │   │   ├── models/
│   │   │   │   ├── user_model.dart
│   │   │   │   ├── farmer_model.dart
│   │   │   │   ├── farm_model.dart
│   │   │   │   ├── crop_model.dart
│   │   │   │   ├── soil_model.dart
│   │   │   │   ├── weather_model.dart
│   │   │   │   ├── prediction_model.dart
│   │   │   │   ├── irrigation_model.dart
│   │   │   │   └── water_use_model.dart
│   │   │   │
│   │   │   ├── repositories/
│   │   │   │   ├── auth_repository.dart
│   │   │   │   ├── farm_repository.dart
│   │   │   │   ├── crop_repository.dart
│   │   │   │   ├── soil_repository.dart
│   │   │   │   ├── weather_repository.dart
│   │   │   │   ├── prediction_repository.dart
│   │   │   │   └── water_use_repository.dart
│   │   │   │
│   │   │   └── services/
│   │   │       ├── api_service.dart
│   │   │       ├── auth_service.dart
│   │   │       ├── storage_service.dart
│   │   │       └── network_service.dart
│   │   │
│   │   ├── domain/
│   │   │   ├── entities/
│   │   │   │   ├── user.dart
│   │   │   │   ├── farmer.dart
│   │   │   │   ├── farm.dart
│   │   │   │   ├── crop.dart
│   │   │   │   ├── soil.dart
│   │   │   │   ├── weather.dart
│   │   │   │   ├── prediction.dart
│   │   │   │   └── irrigation.dart
│   │   │   │
│   │   │   └── usecases/
│   │   │       ├── login_usecase.dart
│   │   │       ├── register_usecase.dart
│   │   │       ├── get_farms_usecase.dart
│   │   │       ├── create_farm_usecase.dart
│   │   │       ├── get_crops_usecase.dart
│   │   │       ├── predict_cwr_usecase.dart
│   │   │       └── get_predictions_usecase.dart
│   │   │
│   │   ├── presentation/
│   │   │   ├── pages/
│   │   │   │   ├── splash_page.dart
│   │   │   │   ├── login_page.dart
│   │   │   │   ├── register_page.dart
│   │   │   │   ├── home_page.dart
│   │   │   │   ├── farm_list_page.dart
│   │   │   │   ├── add_farm_page.dart
│   │   │   │   ├── crop_selection_page.dart
│   │   │   │   ├── soil_info_page.dart
│   │   │   │   ├── weather_dashboard_page.dart
│   │   │   │   ├── cwr_prediction_page.dart
│   │   │   │   ├── prediction_result_page.dart
│   │   │   │   ├── irrigation_advisory_page.dart
│   │   │   │   ├── water_use_tracking_page.dart
│   │   │   │   ├── analytics_page.dart
│   │   │   │   ├── history_page.dart
│   │   │   │   ├── data_quality_page.dart
│   │   │   │   ├── growth_stage_page.dart
│   │   │   │   ├── settings_page.dart
│   │   │   │   └── admin_dashboard_page.dart
│   │   │   │
│   │   │   ├── widgets/
│   │   │   │   ├── common/
│   │   │   │   │   ├── custom_button.dart
│   │   │   │   │   ├── custom_textfield.dart
│   │   │   │   │   ├── custom_card.dart
│   │   │   │   │   ├── loading_indicator.dart
│   │   │   │   │   └── error_widget.dart
│   │   │   │   ├── charts/
│   │   │   │   │   ├── cwr_trend_chart.dart
│   │   │   │   │   ├── rainfall_chart.dart
│   │   │   │   │   ├── water_use_chart.dart
│   │   │   │   │   └── feature_importance_chart.dart
│   │   │   │   ├── farm/
│   │   │   │   │   ├── farm_card.dart
│   │   │   │   │   └── farm_list_item.dart
│   │   │   │   └── prediction/
│   │   │   │       ├── prediction_card.dart
│   │   │   │       └── advisory_card.dart
│   │   │   │
│   │   │   ├── providers/
│   │   │   │   ├── auth_provider.dart
│   │   │   │   ├── farm_provider.dart
│   │   │   │   ├── crop_provider.dart
│   │   │   │   ├── weather_provider.dart
│   │   │   │   ├── prediction_provider.dart
│   │   │   │   └── analytics_provider.dart
│   │   │   │
│   │   │   └── screens/
│   │   │       └── [screen-specific widgets]
│   │   │
│   │   └── routes/
│   │       ├── app_routes.dart
│   │       └── route_generator.dart
│   │
│   ├── assets/
│   │   ├── images/
│   │   ├── icons/
│   │   └── fonts/
│   │
│   ├── test/
│   │   ├── unit/
│   │   ├── widget/
│   │   └── integration/
│   │
│   ├── android/
│   ├── ios/
│   ├── web/
│   ├── pubspec.yaml
│   └── analysis_options.yaml
│
├── backend/                           # FastAPI Backend
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   │
│   │   ├── config/
│   │   │   ├── __init__.py
│   │   │   ├── settings.py
│   │   │   ├── logging.py
│   │   │   └── constants.py
│   │   │
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── deps.py
│   │   │   │
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       ├── api.py
│   │   │       │
│   │   │       └── endpoints/
│   │   │           ├── __init__.py
│   │   │           ├── auth.py
│   │   │           ├── farmers.py
│   │   │           ├── farms.py
│   │   │           ├── crops.py
│   │   │           ├── soil.py
│   │   │           ├── weather.py
│   │   │           ├── predictions.py
│   │   │           ├── irrigation.py
│   │   │           ├── water_use.py
│   │   │           ├── analytics.py
│   │   │           ├── advisory.py
│   │   │           ├── data_quality.py
│   │   │           └── admin.py
│   │   │
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── security.py
│   │   │   ├── config.py
│   │   │   ├── exceptions.py
│   │   │   └── middleware.py
│   │   │
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── farmer.py
│   │   │   ├── farm.py
│   │   │   ├── field.py
│   │   │   ├── crop.py
│   │   │   ├── crop_growth_stage.py
│   │   │   ├── soil.py
│   │   │   ├── weather.py
│   │   │   ├── rainfall.py
│   │   │   ├── prediction.py
│   │   │   ├── irrigation.py
│   │   │   ├── water_use.py
│   │   │   ├── model_version.py
│   │   │   ├── data_quality_alert.py
│   │   │   └── advisory.py
│   │   │
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── farmer.py
│   │   │   ├── farm.py
│   │   │   ├── field.py
│   │   │   ├── crop.py
│   │   │   ├── crop_growth_stage.py
│   │   │   ├── soil.py
│   │   │   ├── weather.py
│   │   │   ├── rainfall.py
│   │   │   ├── prediction.py
│   │   │   ├── irrigation.py
│   │   │   ├── water_use.py
│   │   │   ├── model_version.py
│   │   │   ├── data_quality_alert.py
│   │   │   └── advisory.py
│   │   │
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py
│   │   │   ├── farmer_service.py
│   │   │   ├── farm_service.py
│   │   │   ├── crop_service.py
│   │   │   ├── soil_service.py
│   │   │   ├── weather_service.py
│   │   │   ├── rainfall_service.py
│   │   │   ├── prediction_service.py
│   │   │   ├── irrigation_service.py
│   │   │   ├── water_use_service.py
│   │   │   ├── advisory_service.py
│   │   │   ├── anomaly_service.py
│   │   │   └── ml_service.py
│   │   │
│   │   ├── database/
│   │   │   ├── __init__.py
│   │   │   ├── connection.py
│   │   │   ├── base.py
│   │   │   ├── session.py
│   │   │   └── repositories/
│   │   │       ├── __init__.py
│   │   │       ├── user_repository.py
│   │   │       ├── farmer_repository.py
│   │   │       ├── farm_repository.py
│   │   │       ├── crop_repository.py
│   │   │       ├── soil_repository.py
│   │   │       ├── weather_repository.py
│   │   │       ├── prediction_repository.py
│   │   │       └── water_use_repository.py
│   │   │
│   │   └── ml/
│   │       ├── __init__.py
│   │       ├── inference.py
│   │       ├── feature_engineering.py
│   │       ├── model_loader.py
│   │       └── predictor.py
│   │
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── unit/
│   │   │   ├── test_auth.py
│   │   │   ├── test_farms.py
│   │   │   ├── test_predictions.py
│   │   │   └── test_services.py
│   │   ├── integration/
│   │   │   ├── test_api.py
│   │   │   └── test_database.py
│   │   └── fixtures/
│   │       └── test_data.py
│   │
│   ├── alembic/
│   │   ├── versions/
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── alembic.ini
│   │
│   ├── scripts/
│   │   ├── seed_database.py
│   │   └── migrate_data.py
│   │
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── pyproject.toml
│   └── Dockerfile
│
├── ml/                               # ML Pipeline (Separate from Backend)
│   ├── __init__.py
│   │
│   ├── data/
│   │   ├── raw/
│   │   │   ├── crop_data.csv
│   │   │   ├── soil_data.csv
│   │   │   ├── weather_data.csv
│   │   │   ├── rainfall_data.csv
│   │   │   └── growth_stage_data.csv
│   │   ├── processed/
│   │   ├── features/
│   │   └── splits/
│   │       ├── train.csv
│   │       ├── val.csv
│   │       └── test.csv
│   │
│   ├── preprocessing/
│   │   ├── __init__.py
│   │   ├── data_loader.py
│   │   ├── data_cleaner.py
│   │   ├── missing_value_handler.py
│   │   ├── outlier_detector.py
│   │   └── data_validator.py
│   │
│   ├── feature_engineering/
│   │   ├── __init__.py
│   │   ├── weather_features.py
│   │   ├── soil_features.py
│   │   ├── crop_features.py
│   │   ├── temporal_features.py
│   │   ├── feature_selector.py
│   │   └── feature_scaler.py
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── base_model.py
│   │   ├── baseline.py
│   │   ├── linear_regression.py
│   │   ├── random_forest.py
│   │   ├── gradient_boosting.py
│   │   ├── xgboost_model.py
│   │   └── lightgbm_model.py
│   │
│   ├── training/
│   │   ├── __init__.py
│   │   ├── train.py
│   │   ├── hyperparameter_tuning.py
│   │   ├── cross_validation.py
│   │   └── model_saver.py
│   │
│   ├── evaluation/
│   │   ├── __init__.py
│   │   ├── metrics.py
│   │   ├── model_comparison.py
│   │   ├── error_analysis.py
│   │   └── validation.py
│   │
│   ├── explainability/
│   │   ├── __init__.py
│   │   ├── feature_importance.py
│   │   ├── shap_explainer.py
│   │   └── prediction_explainer.py
│   │
│   ├── inference/
│   │   ├── __init__.py
│   │   ├── predictor.py
│   │   ├── batch_predictor.py
│   │   └── api_predictor.py
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── logger.py
│   │   └── helpers.py
│   │
│   ├── notebooks/
│   │   ├── 01_eda.ipynb
│   │   ├── 02_feature_engineering.ipynb
│   │   ├── 03_model_training.ipynb
│   │   ├── 04_model_evaluation.ipynb
│   │   └── 05_explainability.ipynb
│   │
│   ├── saved_models/
│   │   ├── baseline_model.pkl
│   │   ├── best_model.pkl
│   │   ├── feature_scaler.pkl
│   │   └── model_metadata.json
│   │
│   ├── requirements.txt
│   └── README.md
│
├── datasets/                         # Dataset Storage
│   ├── crop/
│   │   ├── crop_catalog.csv
│   │   ├── crop_varieties.csv
│   │   └── crop_kc_values.csv
│   ├── soil/
│   │   ├── soil_types.csv
│   │   ├── soil_parameters.csv
│   │   └── district_soil_mapping.csv
│   ├── weather/
│   │   ├── historical_weather.csv
│   │   └── weather_stations.csv
│   ├── rainfall/
│   │   ├── historical_rainfall.csv
│   │   └── district_rainfall.csv
│   ├── growth_stage/
│   │   ├── crop_growth_stages.csv
│   │   └── stage_kc_values.csv
│   └── reference/
│       ├── et0_reference.csv
│       ├── irrigation_efficiency.csv
│       └── crop_water_requirement_reference.csv
│
├── docker/
│   ├── frontend.Dockerfile
│   ├── backend.Dockerfile
│   ├── ml.Dockerfile
│   ├── nginx.conf
│   └── docker-compose.prod.yml
│
├── docs/
│   ├── 01-system-architecture.md
│   ├── 02-folder-structure.md
│   ├── 03-database-schema.md
│   ├── 04-api-design.md
│   ├── 05-ml-pipeline.md
│   ├── 06-flutter-architecture.md
│   ├── 07-dataset-ingestion.md
│   ├── 08-cloud-architecture.md
│   ├── 09-devops-architecture.md
│   ├── 10-implementation-roadmap.md
│   ├── api-documentation.md
│   ├── deployment-guide.md
│   └── research-report.md
│
├── scripts/
│   ├── setup.sh
│   ├── setup_dev.sh
│   ├── run_tests.sh
│   ├── build_docker.sh
│   └── deploy.sh
│
├── .github/
│   └── workflows/
│       ├── ci.yml
│       ├── cd.yml
│       └── test.yml
│
└── tests/
    ├── integration/
    └── e2e/
```

---

## Folder Purpose Summary

### `/frontend` - Flutter Application
- **Purpose**: Mobile and web application for farmers
- **Key Components**: UI, state management, API integration, local storage
- **Target**: Android (primary), Web (secondary)

### `/backend` - FastAPI Backend
- **Purpose**: REST API, business logic, database operations
- **Key Components**: API endpoints, services, repositories, authentication
- **Responsibilities**: Data management, ML orchestration, external API integration

### `/ml` - Machine Learning Pipeline
- **Purpose**: Data preprocessing, model training, evaluation, inference
- **Key Components**: Data processing, feature engineering, models, evaluation
- **Independence**: Separate from backend for research reproducibility

### `/datasets` - Dataset Storage
- **Purpose**: Store all agricultural datasets
- **Categories**: Crop, soil, weather, rainfall, growth stage, reference data
- **Format**: CSV, JSON (configurable)

### `/docker` - Containerization
- **Purpose**: Docker configurations for all services
- **Components**: Dockerfiles, docker-compose, nginx config

### `/docs` - Documentation
- **Purpose**: Architecture, API docs, deployment guides, research documentation
- **Audience**: Developers, researchers, project evaluators

### `/scripts` - Utility Scripts
- **Purpose**: Setup, testing, deployment automation
- **Usage**: Development and CI/CD pipelines

---

## File Naming Conventions

### Python (Backend/ML)
- Modules: `snake_case.py`
- Classes: `PascalCase`
- Functions: `snake_case`
- Constants: `UPPER_SNAKE_CASE`

### Dart (Flutter)
- Files: `snake_case.dart`
- Classes: `PascalCase`
- Functions/Methods: `camelCase`
- Constants: `lowerCamelCase` or `UPPER_SNAKE_CASE`

### Documentation
- Files: `kebab-case.md`
- Sections: Numbered with descriptive titles

---

## Configuration Files

### Root Level
- `.env.example` - Environment variable template
- `docker-compose.yml` - Local development orchestration
- `.gitignore` - Git ignore rules
- `README.md` - Project overview

### Backend
- `requirements.txt` - Production dependencies
- `requirements-dev.txt` - Development dependencies
- `pyproject.toml` - Python project configuration
- `alembic.ini` - Database migration configuration

### Frontend
- `pubspec.yaml` - Flutter dependencies
- `analysis_options.yaml` - Dart linting rules

---

## Important Notes

1. **ML Independence**: The `/ml` directory is separate from `/backend` to ensure research reproducibility and independent model updates.

2. **Dataset Separation**: Datasets are stored separately to allow easy updates without code changes.

3. **Documentation**: All architecture decisions are documented in `/docs` for academic evaluation.

4. **Testing**: Each major component has its own test directory.

5. **Docker**: Each service has its own Dockerfile for independent deployment.

6. **Environment**: `.env.example` provides template for environment variables without exposing secrets.
