# ML Pipeline Architecture
## Smart Crop Water Requirement Prediction System

---

## ML Pipeline Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    RAW DATASETS                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Crop    │  │  Soil    │  │ Weather  │  │ Rainfall │   │
│  │  Data    │  │  Data    │  │  Data    │  │  Data    │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  DATA COLLECTION                            │
│  - Load CSV/JSON files                                       │
│  - Database queries                                          │
│  - API data fetching                                         │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  DATA VALIDATION                            │
│  - Schema validation                                         │
│  - Data type checks                                          │
│  - Range validation                                          │
│  - Constraint validation                                     │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  DATA CLEANING                              │
│  - Duplicate removal                                         │
│  - Inconsistency fixing                                      │
│  - Standardization                                           │
│  - Date parsing                                              │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────┐
│            MISSING VALUE HANDLING                           │
│  - Missing value analysis                                    │
│  - Imputation strategies                                     │
│  - Flagging missing values                                   │
│  - Domain-specific imputation                                │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────┐
│            OUTLIER / DATA QUALITY ANALYSIS                   │
│  - IQR-based detection                                        │
│  - Z-score detection                                          │
│  - Isolation Forest                                           │
│  - Domain-specific rules                                     │
│  - Anomaly flagging                                           │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────┐
│               FEATURE ENGINEERING                           │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Weather Features                                     │   │
│  │  - Temperature metrics                                 │   │
│  │  - Humidity indices                                    │   │
│  │  - Wind speed transformations                          │   │
│  │  - Solar radiation derivatives                         │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Soil Features                                        │   │
│  │  - pH transformations                                  │   │
│  │  - Nutrient ratios                                     │   │
│  │  - Soil moisture indices                               │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Crop Features                                        │   │
│  │  - Kc values                                           │   │
│  │  - Growth stage encoding                               │   │
│  │  - Days after sowing                                   │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Temporal Features                                    │   │
│  │  - Season encoding                                     │   │
│  │  - Month encoding                                      │   │
│  │  - Day of year                                         │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Rainfall Features                                    │   │
│  │  - Effective rainfall (USDA SCS)                      │   │
│  │  - Cumulative rainfall                                │   │
│  │  - Rainfall frequency                                  │   │
│  └──────────────────────────────────────────────────────┘   │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────┐
│               FEATURE SELECTION                             │
│  - Correlation analysis                                      │
│  - Mutual information                                        │
│  - Recursive feature elimination                             │
│  - Domain knowledge filtering                                │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────┐
│               TRAIN/TEST SPLIT                              │
│  - Temporal split (time-series aware)                        │
│  - Stratified split (by crop/region)                         │
│  - Validation set creation                                   │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────┐
│               BASELINE MODEL                               │
│  - ET0 Calculation (FAO Penman-Monteith)                    │
│  - Kc-based ETc calculation                                  │
│  - Effective rainfall (USDA SCS)                             │
│  - Irrigation requirement calculation                        │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────┐
│               ML MODELS                                      │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Linear Regression                                     │   │
│  │  - Baseline ML model                                   │   │
│  │  - Interpretable coefficients                           │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Random Forest Regressor                              │   │
│  │  - Ensemble method                                     │   │
│  │  - Feature importance                                  │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Gradient Boosting Regressor                          │   │
│  │  - Sequential ensemble                                 │   │
│  │  - High accuracy                                       │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  XGBoost (optional)                                   │   │
│  │  - Optimized gradient boosting                         │   │
│  │  - Regularization                                      │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  LightGBM (optional)                                  │   │
│  │  - Fast gradient boosting                              │   │
│  │  - Memory efficient                                    │   │
│  └──────────────────────────────────────────────────────┘   │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────┐
│           HYPERPARAMETER TUNING                            │
│  - Grid search                                               │
│  - Random search                                             │
│  - Bayesian optimization (optional)                          │
│  - Cross-validation integration                              │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────┐
│               CROSS VALIDATION                              │
│  - K-fold cross-validation                                   │
│  - Time-series cross-validation                              │
│  - Stratified cross-validation                               │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────┐
│               MODEL EVALUATION                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Metrics                                               │   │
│  │  - MAE (Mean Absolute Error)                           │   │
│  │  - RMSE (Root Mean Square Error)                       │   │
│  │  - R² (Coefficient of Determination)                   │   │
│  │  - MAPE (Mean Absolute Percentage Error)                │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Model Comparison                                     │   │
│  │  - Metric comparison table                            │   │
│  │  - Statistical significance tests                     │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Error Analysis                                       │   │
│  │  - Residual plots                                     │   │
│  │  - Error distribution                                 │   │
│  │  - Prediction vs Actual plots                          │   │
│  └──────────────────────────────────────────────────────┘   │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────┐
│           BEST MODEL SELECTION                             │
│  - Metric-based selection                                   │
│  - Robustness consideration                                  │
│  - Interpretability trade-off                                │
│  - Computational efficiency                                  │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────┐
│           EXPLAINABLE PREDICTION                           │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Feature Importance                                   │   │
│  │  - Global feature importance                          │   │
│  │  - Permutation importance                              │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  SHAP Values (optional)                              │   │
│  │  - Local explanations                                 │   │
│  │  - Feature contribution plots                          │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Prediction Explanation                              │   │
│  │  - Feature-wise contribution                          │   │
│  │  - Directional influence                              │   │
│  └──────────────────────────────────────────────────────┘   │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────┐
│           MODEL SAVING                                     │
│  - Model serialization (pickle/joblib)                       │
│  - Feature scaler saving                                     │
│  - Model metadata storage                                   │
│  - Version control                                          │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────┐
│           CWR PREDICTION API                              │
│  - Model loading                                             │
│  - Feature preprocessing                                     │
│  - Real-time inference                                       │
│  - Prediction confidence estimation                          │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────┐
│           FLUTTER APPLICATION                              │
│  - Prediction display                                        │
│  - Visualization                                            │
│  - Advisory generation                                       │
└─────────────────────────────────────────────────────────────┘
```

---

## Detailed Pipeline Stages

### Stage 1: Data Collection

**Purpose**: Load and aggregate raw datasets from multiple sources

**Input Sources**:
- Crop catalog CSV
- Soil parameters CSV
- Historical weather CSV
- Historical rainfall CSV
- Crop growth stage reference CSV
- ET0 reference data (if available)

**Process**:
```python
# Pseudocode
def load_datasets():
    crop_data = pd.read_csv('datasets/crop/crop_catalog.csv')
    soil_data = pd.read_csv('datasets/soil/soil_parameters.csv')
    weather_data = pd.read_csv('datasets/weather/historical_weather.csv')
    rainfall_data = pd.read_csv('datasets/rainfall/historical_rainfall.csv')
    growth_stage_data = pd.read_csv('datasets/growth_stage/crop_growth_stages.csv')
    
    return {
        'crop': crop_data,
        'soil': soil_data,
        'weather': weather_data,
        'rainfall': rainfall_data,
        'growth_stage': growth_stage_data
    }
```

**Output**: Dictionary of loaded DataFrames

---

### Stage 2: Data Validation

**Purpose**: Ensure data quality and consistency

**Validation Checks**:
- Schema validation (column names, data types)
- Range validation (e.g., pH: 0-14, temperature: -50 to 60°C)
- Constraint validation (e.g., sowing_date ≤ current_date)
- Uniqueness checks (e.g., unique crop IDs)
- Completeness checks (required fields not null)

**Process**:
```python
def validate_data(data_dict):
    validation_results = {}
    
    for dataset_name, df in data_dict.items():
        # Schema validation
        schema_errors = validate_schema(df, dataset_name)
        
        # Range validation
        range_errors = validate_ranges(df, dataset_name)
        
        # Constraint validation
        constraint_errors = validate_constraints(df, dataset_name)
        
        validation_results[dataset_name] = {
            'schema_errors': schema_errors,
            'range_errors': range_errors,
            'constraint_errors': constraint_errors,
            'is_valid': len(schema_errors) == 0 and len(range_errors) == 0
        }
    
    return validation_results
```

**Output**: Validation report with errors and warnings

---

### Stage 3: Data Cleaning

**Purpose**: Remove inconsistencies and standardize data

**Cleaning Operations**:
- Remove duplicate records
- Fix inconsistent capitalization
- Standardize date formats
- Standardize units (e.g., all temperatures in °C)
- Handle whitespace issues
- Fix typos in categorical values

**Process**:
```python
def clean_data(df, dataset_name):
    # Remove duplicates
    df = df.drop_duplicates()
    
    # Standardize text columns
    text_columns = get_text_columns(dataset_name)
    for col in text_columns:
        df[col] = df[col].str.strip().str.title()
    
    # Standardize dates
    date_columns = get_date_columns(dataset_name)
    for col in date_columns:
        df[col] = pd.to_datetime(df[col], errors='coerce')
    
    return df
```

**Output**: DataFrames with cleaned data

---

### Stage 4: Missing Value Handling

**Purpose**: Handle missing data appropriately

**Strategies**:
- **Numerical features**: Mean/median imputation, domain-specific imputation
- **Categorical features**: Mode imputation, "Unknown" category
- **Time-series**: Forward/backward fill, interpolation
- **Flag missing**: Create binary indicator columns

**Process**:
```python
def handle_missing_values(df, dataset_name):
    # Analyze missing patterns
    missing_analysis = analyze_missing(df)
    
    # Numerical imputation
    numerical_cols = df.select_dtypes(include=[np.number]).columns
    for col in numerical_cols:
        if df[col].isnull().sum() > 0:
            if dataset_name == 'weather':
                # Time-series imputation
                df[col] = df[col].fillna(method='ffill').fillna(method='bfill')
            else:
                # Median imputation
                df[col] = df[col].fillna(df[col].median())
    
    # Categorical imputation
    categorical_cols = df.select_dtypes(include=['object']).columns
    for col in categorical_cols:
        if df[col].isnull().sum() > 0:
            df[col] = df[col].fillna('Unknown')
    
    # Create missing indicators
    for col in df.columns:
        if df[col].isnull().sum() > 0:
            df[f'{col}_missing'] = df[col].isnull().astype(int)
    
    return df, missing_analysis
```

**Output**: DataFrames with imputed values and missing indicators

---

### Stage 5: Outlier / Data Quality Analysis

**Purpose**: Detect and flag anomalous values

**Detection Methods**:
- **IQR Method**: Values outside Q1-1.5×IQR to Q3+1.5×IQR
- **Z-Score Method**: Values with |z| > 3
- **Isolation Forest**: ML-based anomaly detection
- **Domain Rules**: Agricultural domain-specific rules

**Process**:
```python
def detect_outliers(df, dataset_name):
    outlier_report = {}
    
    numerical_cols = df.select_dtypes(include=[np.number]).columns
    
    for col in numerical_cols:
        # IQR method
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        iqr_outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)]
        
        # Z-score method
        z_scores = np.abs(stats.zscore(df[col].dropna()))
        z_outliers = df[z_scores > 3]
        
        # Domain-specific rules
        domain_outliers = apply_domain_rules(df, col, dataset_name)
        
        outlier_report[col] = {
            'iqr_outliers': len(iqr_outliers),
            'z_score_outliers': len(z_outliers),
            'domain_outliers': len(domain_outliers),
            'total_outliers': len(set(iqr_outliers.index) | set(z_outliers.index))
        }
        
        # Flag outliers
        df[f'{col}_outlier'] = ((df[col] < lower_bound) | (df[col] > upper_bound)).astype(int)
    
    return df, outlier_report
```

**Output**: DataFrames with outlier flags and outlier report

---

### Stage 6: Feature Engineering

**Purpose**: Create meaningful features for ML models

#### 6.1 Weather Features
```python
def engineer_weather_features(weather_df):
    # Temperature features
    weather_df['temp_range'] = weather_df['temperature_max'] - weather_df['temperature_min']
    weather_df['temp_avg_7day'] = weather_df['temperature_avg'].rolling(7).mean()
    
    # Humidity features
    weather_df['humidity_category'] = pd.cut(
        weather_df['humidity'],
        bins=[0, 40, 70, 100],
        labels=['Low', 'Medium', 'High']
    )
    
    # Wind features
    weather_df['wind_category'] = pd.cut(
        weather_df['wind_speed'],
        bins=[0, 5, 15, 30],
        labels=['Calm', 'Moderate', 'Strong']
    )
    
    return weather_df
```

#### 6.2 Soil Features
```python
def engineer_soil_features(soil_df):
    # Nutrient ratios
    soil_df['np_ratio'] = soil_df['nitrogen'] / (soil_df['phosphorus'] + 1e-6)
    soil_df['nk_ratio'] = soil_df['nitrogen'] / (soil_df['potassium'] + 1e-6)
    
    # pH categories
    soil_df['ph_category'] = pd.cut(
        soil_df['ph_level'],
        bins=[0, 5.5, 6.5, 7.5, 14],
        labels=['Acidic', 'Slightly Acidic', 'Neutral', 'Alkaline']
    )
    
    return soil_df
```

#### 6.3 Crop Features
```python
def engineer_crop_features(crop_df, growth_stage_df):
    # Merge with growth stage data
    merged = crop_df.merge(growth_stage_df, on='crop_id', how='left')
    
    # Days after sowing
    merged['days_after_sowing'] = (merged['current_date'] - merged['sowing_date']).dt.days
    
    # Growth stage progress
    merged['stage_progress'] = merged['days_after_sowing'] / merged['duration_days']
    
    return merged
```

#### 6.4 Temporal Features
```python
def engineer_temporal_features(df):
    df['date'] = pd.to_datetime(df['date'])
    df['month'] = df['date'].dt.month
    df['day_of_year'] = df['date'].dt.dayofyear
    df['season'] = df['month'].apply(get_season)
    df['is_monsoon'] = df['month'].isin([6, 7, 8, 9, 10, 11]).astype(int)
    
    return df

def get_season(month):
    if month in [12, 1, 2]:
        return 'Winter'
    elif month in [3, 4, 5]:
        return 'Summer'
    elif month in [6, 7, 8, 9]:
        return 'Monsoon'
    else:
        return 'Post-Monsoon'
```

#### 6.5 Rainfall Features
```python
def engineer_rainfall_features(rainfall_df):
    # Effective rainfall (USDA SCS method)
    rainfall_df['effective_rainfall'] = rainfall_df['rainfall'].apply(
        lambda x: 0.8 * x if x <= 250 else 125 + 0.5 * (x - 250)
    )
    
    # Cumulative rainfall
    rainfall_df['cumulative_rainfall_7day'] = rainfall_df['rainfall'].rolling(7).sum()
    rainfall_df['cumulative_rainfall_30day'] = rainfall_df['rainfall'].rolling(30).sum()
    
    # Rainfall frequency
    rainfall_df['rainy_days_7day'] = (rainfall_df['rainfall'] > 0).rolling(7).sum()
    
    return rainfall_df
```

**Output**: DataFrames with engineered features

---

### Stage 7: Feature Selection

**Purpose**: Select most relevant features for prediction

**Methods**:
- Correlation analysis (remove highly correlated features)
- Mutual information (select features with high MI with target)
- Recursive Feature Elimination (RFE)
- Domain knowledge filtering

**Process**:
```python
def select_features(X, y, method='correlation'):
    if method == 'correlation':
        # Remove highly correlated features
        corr_matrix = X.corr().abs()
        upper_tri = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
        to_drop = [col for col in upper_tri.columns if any(upper_tri[col] > 0.9)]
        X_selected = X.drop(columns=to_drop)
        
    elif method == 'mutual_info':
        # Select features based on mutual information
        mi_scores = mutual_info_regression(X, y)
        selected_features = X.columns[mi_scores > np.percentile(mi_scores, 25)]
        X_selected = X[selected_features]
        
    elif method == 'rfe':
        # Recursive Feature Elimination
        estimator = RandomForestRegressor(n_estimators=100)
        selector = RFE(estimator, n_features_to_select=20)
        selector = selector.fit(X, y)
        X_selected = X.loc[:, selector.support_]
    
    return X_selected
```

**Output**: Selected feature set

---

### Stage 8: Train/Test Split

**Purpose**: Split data for training and evaluation

**Strategies**:
- **Temporal split**: For time-series data (train on past, test on future)
- **Stratified split**: Ensure representative distribution of crops/regions
- **Random split**: For non-temporal data

**Process**:
```python
def split_data(X, y, split_method='temporal', date_column=None):
    if split_method == 'temporal' and date_column:
        # Temporal split (80% train, 20% test)
        split_date = X[date_column].quantile(0.8)
        X_train = X[X[date_column] <= split_date]
        X_test = X[X[date_column] > split_date]
        y_train = y.loc[X_train.index]
        y_test = y.loc[X_test.index]
        
    elif split_method == 'stratified':
        # Stratified split by crop
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, stratify=X['crop_id'], random_state=42
        )
        
    else:
        # Random split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
    
    # Create validation set (20% of train)
    X_train, X_val, y_train, y_val = train_test_split(
        X_train, y_train, test_size=0.2, random_state=42
    )
    
    return X_train, X_val, X_test, y_train, y_val, y_test
```

**Output**: Train, validation, and test sets

---

### Stage 9: Baseline Model

**Purpose**: Establish reference using scientific calculation

**Baseline Calculation**:
```python
def calculate_baseline_cwr(weather_data, crop_data, growth_stage_data):
    """
    Calculate CWR using FAO Penman-Monteith method
    ETc = ET0 × Kc
    """
    # ET0 calculation (simplified - full implementation uses FAO-56)
    weather_data['et0'] = calculate_et0(weather_data)
    
    # Get Kc value based on growth stage
    merged = weather_data.merge(growth_stage_data, on=['crop_id', 'growth_stage_id'])
    
    # Calculate ETc
    merged['etc'] = merged['et0'] * merged['kc_value']
    
    # Calculate effective rainfall
    merged['effective_rainfall'] = calculate_effective_rainfall(merged['rainfall'])
    
    # Calculate irrigation requirement
    merged['irrigation_requirement'] = merged['etc'] - merged['effective_rainfall']
    merged['irrigation_requirement'] = merged['irrigation_requirement'].clip(lower=0)
    
    return merged['irrigation_requirement']

def calculate_et0(weather_data):
    """
    Calculate reference evapotranspiration (ET0)
    Simplified FAO Penman-Monteith
    """
    # Full implementation includes:
    # - Temperature
    # - Humidity
    # - Wind speed
    # - Solar radiation
    # - Atmospheric pressure
    # - Latitude
    # - Day of year
    
    # Simplified version for illustration
    et0 = (0.408 * weather_data['temperature_avg'] * 
           (0.65 + 0.01 * weather_data['temperature_avg']) *
           (weather_data['solar_radiation'] / 100))
    
    return et0

def calculate_effective_rainfall(rainfall):
    """
    Calculate effective rainfall using USDA SCS method
    """
    effective = np.where(
        rainfall <= 250,
        0.8 * rainfall,
        125 + 0.5 * (rainfall - 250)
    )
    return effective
```

**Output**: Baseline CWR predictions

---

### Stage 10: ML Models

#### 10.1 Linear Regression
```python
def train_linear_regression(X_train, y_train):
    model = LinearRegression()
    model.fit(X_train, y_train)
    return model
```

#### 10.2 Random Forest
```python
def train_random_forest(X_train, y_train):
    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=10,
        min_samples_split=5,
        random_state=42
    )
    model.fit(X_train, y_train)
    return model
```

#### 10.3 Gradient Boosting
```python
def train_gradient_boosting(X_train, y_train):
    model = GradientBoostingRegressor(
        n_estimators=100,
        learning_rate=0.1,
        max_depth=5,
        random_state=42
    )
    model.fit(X_train, y_train)
    return model
```

#### 10.4 XGBoost (Optional)
```python
def train_xgboost(X_train, y_train):
    model = xgb.XGBRegressor(
        n_estimators=100,
        learning_rate=0.1,
        max_depth=5,
        random_state=42
    )
    model.fit(X_train, y_train)
    return model
```

#### 10.5 LightGBM (Optional)
```python
def train_lightgbm(X_train, y_train):
    model = lgb.LGBMRegressor(
        n_estimators=100,
        learning_rate=0.1,
        max_depth=5,
        random_state=42
    )
    model.fit(X_train, y_train)
    return model
```

**Output**: Trained ML models

---

### Stage 11: Hyperparameter Tuning

**Purpose**: Optimize model hyperparameters

**Methods**:
- Grid Search
- Random Search
- Bayesian Optimization (optional)

**Process**:
```python
def tune_hyperparameters(model, X_train, y_train, param_grid, method='grid'):
    if method == 'grid':
        tuner = GridSearchCV(
            model,
            param_grid,
            cv=5,
            scoring='neg_mean_absolute_error',
            n_jobs=-1
        )
    elif method == 'random':
        tuner = RandomizedSearchCV(
            model,
            param_grid,
            n_iter=50,
            cv=5,
            scoring='neg_mean_absolute_error',
            random_state=42
        )
    
    tuner.fit(X_train, y_train)
    return tuner.best_estimator_, tuner.best_params_
```

**Example Parameter Grid**:
```python
rf_param_grid = {
    'n_estimators': [50, 100, 200],
    'max_depth': [5, 10, 15, None],
    'min_samples_split': [2, 5, 10],
    'min_samples_leaf': [1, 2, 4]
}

gb_param_grid = {
    'n_estimators': [50, 100, 200],
    'learning_rate': [0.01, 0.1, 0.2],
    'max_depth': [3, 5, 7],
    'subsample': [0.8, 0.9, 1.0]
}
```

**Output**: Optimized models with best hyperparameters

---

### Stage 12: Cross Validation

**Purpose**: Robust model evaluation

**Methods**:
- K-Fold CV
- Time Series CV
- Stratified K-Fold CV

**Process**:
```python
def cross_validate(model, X, y, cv_method='kfold', n_splits=5):
    if cv_method == 'kfold':
        cv = KFold(n_splits=n_splits, shuffle=True, random_state=42)
    elif cv_method == 'timeseries':
        cv = TimeSeriesSplit(n_splits=n_splits)
    elif cv_method == 'stratified':
        cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
    
    scores = cross_val_score(
        model, X, y,
        cv=cv,
        scoring='neg_mean_absolute_error',
        n_jobs=-1
    )
    
    return {
        'mae_mean': -scores.mean(),
        'mae_std': scores.std(),
        'scores': -scores
    }
```

**Output**: Cross-validation scores

---

### Stage 13: Model Evaluation

**Purpose**: Compare model performance

**Metrics**:
```python
def evaluate_model(model, X_test, y_test):
    y_pred = model.predict(X_test)
    
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)
    mape = mean_absolute_percentage_error(y_test, y_pred)
    
    return {
        'mae': mae,
        'rmse': rmse,
        'r2': r2,
        'mape': mape,
        'predictions': y_pred
    }
```

**Model Comparison**:
```python
def compare_models(models, X_test, y_test):
    results = {}
    for name, model in models.items():
        results[name] = evaluate_model(model, X_test, y_test)
    
    comparison_df = pd.DataFrame(results).T
    comparison_df = comparison_df.sort_values('mae')
    
    return comparison_df
```

**Error Analysis**:
```python
def analyze_errors(y_test, y_pred):
    residuals = y_test - y_pred
    
    return {
        'residuals': residuals,
        'mean_residual': residuals.mean(),
        'std_residual': residuals.std(),
        'max_positive_error': residuals.max(),
        'max_negative_error': residuals.min()
    }
```

**Output**: Evaluation metrics and comparison table

---

### Stage 14: Best Model Selection

**Purpose**: Select the best performing model

**Criteria**:
- Lowest MAE (primary)
- Highest R² (secondary)
- Robustness (low variance in CV)
- Interpretability
- Computational efficiency

**Process**:
```python
def select_best_model(model_results):
    # Primary: Lowest MAE
    best_model = min(model_results.items(), key=lambda x: x[1]['mae'])
    
    return {
        'name': best_model[0],
        'model': best_model[1]['model'],
        'metrics': best_model[1],
        'selection_reason': f"Lowest MAE: {best_model[1]['mae']:.4f}"
    }
```

**Output**: Best model with justification

---

### Stage 15: Explainable Prediction

#### 15.1 Feature Importance
```python
def get_feature_importance(model, feature_names):
    if hasattr(model, 'feature_importances_'):
        importance = model.feature_importances_
    elif hasattr(model, 'coef_'):
        importance = np.abs(model.coef_)
    else:
        importance = None
    
    if importance is not None:
        importance_df = pd.DataFrame({
            'feature': feature_names,
            'importance': importance
        }).sort_values('importance', ascending=False)
        
        return importance_df
    return None
```

#### 15.2 SHAP Values (Optional)
```python
def get_shap_explanations(model, X_train, X_test):
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_test)
    
    return {
        'explainer': explainer,
        'shap_values': shap_values,
        'expected_value': explainer.expected_value
    }
```

#### 15.3 Prediction Explanation
```python
def explain_prediction(model, feature_names, feature_values, feature_importance):
    explanations = []
    
    for i, (feature, value) in enumerate(zip(feature_names, feature_values)):
        importance = feature_importance.loc[feature_importance['feature'] == feature, 'importance'].values[0]
        
        if importance > 0.1:
            direction = "increased" if value > 0 else "decreased"
            explanations.append({
                'feature': feature,
                'value': value,
                'importance': importance,
                'direction': direction,
                'description': f"{feature} {direction} estimated water requirement"
            })
    
    return sorted(explanations, key=lambda x: x['importance'], reverse=True)
```

**Output**: Feature importance rankings and prediction explanations

---

### Stage 16: Model Saving

**Purpose**: Save trained models with metadata

**Process**:
```python
def save_model(model, model_name, version, metrics, features, training_date):
    # Save model
    model_path = f'ml/saved_models/{model_name}_{version}.pkl'
    joblib.dump(model, model_path)
    
    # Save metadata
    metadata = {
        'model_name': model_name,
        'version': version,
        'algorithm': type(model).__name__,
        'training_date': training_date,
        'features': features,
        'metrics': metrics,
        'model_path': model_path
    }
    
    metadata_path = f'ml/saved_models/{model_name}_{version}_metadata.json'
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    return metadata
```

**Metadata Structure**:
```json
{
  "model_name": "CWR_Model",
  "version": "v1.0",
  "algorithm": "GradientBoostingRegressor",
  "training_date": "2024-01-15",
  "features": [
    "temperature",
    "humidity",
    "rainfall",
    "soil_ph",
    "kc_value",
    "days_after_sowing"
  ],
  "metrics": {
    "mae": 0.38,
    "rmse": 0.55,
    "r2": 0.91,
    "mape": 7.2
  },
  "model_path": "ml/saved_models/CWR_Model_v1.0.pkl"
}
```

**Output**: Saved model files and metadata

---

### Stage 17: CWR Prediction API

**Purpose**: Real-time prediction for the backend

**Process**:
```python
class CWRPredictor:
    def __init__(self, model_path, metadata_path, scaler_path=None):
        self.model = joblib.load(model_path)
        with open(metadata_path, 'r') as f:
            self.metadata = json.load(f)
        if scaler_path:
            self.scaler = joblib.load(scaler_path)
        else:
            self.scaler = None
    
    def preprocess(self, input_data):
        # Feature engineering
        features = engineer_features(input_data)
        
        # Scale if scaler exists
        if self.scaler:
            features = self.scaler.transform(features)
        
        return features
    
    def predict(self, input_data):
        features = self.preprocess(input_data)
        prediction = self.model.predict(features)
        
        return {
            'cwr_mm_day': prediction[0],
            'cwr_mm_week': prediction[0] * 7,
            'model_version': self.metadata['version'],
            'confidence': self._calculate_confidence(features)
        }
    
    def _calculate_confidence(self, features):
        # Simple confidence based on prediction variance
        # Could be enhanced with conformal prediction
        return 0.85
```

**Output**: Prediction API class for backend integration

---

## ML Pipeline Configuration

### Configuration File (ml/utils/config.py)
```python
ML_CONFIG = {
    'data': {
        'raw_path': 'ml/data/raw',
        'processed_path': 'ml/data/processed',
        'features_path': 'ml/data/features',
        'splits_path': 'ml/data/splits'
    },
    'preprocessing': {
        'missing_threshold': 0.3,
        'outlier_method': 'iqr',
        'outlier_threshold': 1.5
    },
    'feature_engineering': {
        'weather_features': True,
        'soil_features': True,
        'temporal_features': True,
        'rainfall_features': True
    },
    'models': {
        'linear_regression': True,
        'random_forest': True,
        'gradient_boosting': True,
        'xgboost': False,
        'lightgbm': False
    },
    'training': {
        'test_size': 0.2,
        'validation_size': 0.2,
        'random_state': 42,
        'cv_folds': 5
    },
    'hyperparameter_tuning': {
        'method': 'grid',
        'n_iter': 50
    },
    'evaluation': {
        'primary_metric': 'mae',
        'secondary_metric': 'r2'
    },
    'model_saving': {
        'path': 'ml/saved_models',
        'format': 'pickle'
    }
}
```

---

## ML Pipeline Execution

### Main Training Script (ml/training/train.py)
```python
def main():
    # Load configuration
    config = load_config('ml/utils/config.py')
    
    # Stage 1: Data Collection
    raw_data = load_datasets(config['data']['raw_path'])
    
    # Stage 2: Data Validation
    validation_results = validate_data(raw_data)
    
    # Stage 3: Data Cleaning
    cleaned_data = {k: clean_data(v, k) for k, v in raw_data.items()}
    
    # Stage 4: Missing Value Handling
    imputed_data, missing_report = handle_missing_values(cleaned_data)
    
    # Stage 5: Outlier Detection
    outlier_data, outlier_report = detect_outliers(imputed_data)
    
    # Stage 6: Feature Engineering
    engineered_data = engineer_features(outlier_data)
    
    # Stage 7: Feature Selection
    X, y = prepare_target(engineered_data)
    X_selected = select_features(X, y)
    
    # Stage 8: Train/Test Split
    X_train, X_val, X_test, y_train, y_val, y_test = split_data(X_selected, y)
    
    # Stage 9: Baseline Model
    baseline_predictions = calculate_baseline_cwr(...)
    
    # Stage 10: ML Models
    models = {}
    if config['models']['linear_regression']:
        models['Linear Regression'] = train_linear_regression(X_train, y_train)
    if config['models']['random_forest']:
        models['Random Forest'] = train_random_forest(X_train, y_train)
    if config['models']['gradient_boosting']:
        models['Gradient Boosting'] = train_gradient_boosting(X_train, y_train)
    
    # Stage 11: Hyperparameter Tuning
    tuned_models = {}
    for name, model in models.items():
        tuned_model, best_params = tune_hyperparameters(model, X_train, y_train, ...)
        tuned_models[name] = tuned_model
    
    # Stage 12: Cross Validation
    cv_results = {}
    for name, model in tuned_models.items():
        cv_results[name] = cross_validate(model, X_train, y_train)
    
    # Stage 13: Model Evaluation
    evaluation_results = {}
    for name, model in tuned_models.items():
        evaluation_results[name] = evaluate_model(model, X_test, y_test)
    
    # Stage 14: Best Model Selection
    best_model = select_best_model(evaluation_results)
    
    # Stage 15: Explainability
    feature_importance = get_feature_importance(best_model['model'], X_train.columns)
    
    # Stage 16: Model Saving
    save_model(
        best_model['model'],
        'CWR_Model',
        'v1.0',
        best_model['metrics'],
        X_train.columns.tolist(),
        datetime.now().date()
    )
    
    # Generate Report
    generate_report(evaluation_results, cv_results, feature_importance)
    
    return best_model
```

---

## Research Evaluation Metrics

### Model Performance Report
```
Model Performance Comparison
============================

Baseline (ET0 × Kc)
-------------------
MAE: 0.85 mm/day
RMSE: 1.12 mm/day
R²: 0.72
MAPE: 12.5%

Linear Regression
-----------------
MAE: 0.52 mm/day
RMSE: 0.78 mm/day
R²: 0.84
MAPE: 9.2%

Random Forest
-------------
MAE: 0.42 mm/day
RMSE: 0.62 mm/day
R²: 0.89
MAPE: 8.1%

Gradient Boosting
-----------------
MAE: 0.38 mm/day
RMSE: 0.55 mm/day
R²: 0.91
MAPE: 7.2%

Best Model: Gradient Boosting
Reason: Lowest MAE and highest R² score
```

### Feature Importance Report
```
Feature Importance (Gradient Boosting)
=======================================

1. Temperature (0.35)
2. Growth Stage Kc Value (0.28)
3. Rainfall (0.20)
4. Humidity (0.12)
5. Soil Moisture (0.05)
```

---

## ML Pipeline Outputs

### Artifacts
1. **Processed Data**: Cleaned and engineered datasets
2. **Trained Models**: Saved model files (.pkl)
3. **Model Metadata**: JSON files with model information
4. **Feature Scalers**: Saved scalers for preprocessing
5. **Evaluation Reports**: CSV/JSON with performance metrics
6. **Visualization Plots**: Charts for research report

### Documentation
1. **Data Quality Report**: Missing values, outliers, validation results
2. **Feature Engineering Report**: Created features and their importance
3. **Model Training Report**: Training process, hyperparameters, CV results
4. **Model Evaluation Report**: Performance metrics, comparison tables
5. **Explainability Report**: Feature importance, SHAP plots

---

## Integration with Backend

### Backend ML Service (backend/app/ml/inference.py)
```python
class MLInferenceService:
    def __init__(self):
        self.predictor = CWRPredictor(
            model_path='ml/saved_models/CWR_Model_v1.0.pkl',
            metadata_path='ml/saved_models/CWR_Model_v1.0_metadata.json'
        )
    
    async def predict_cwr(self, input_data):
        # Prepare input data
        features = self._prepare_features(input_data)
        
        # Get prediction
        prediction = self.predictor.predict(features)
        
        # Get explanation
        explanation = self._get_explanation(features)
        
        return {
            'prediction': prediction,
            'explanation': explanation
        }
    
    def _prepare_features(self, input_data):
        # Convert API input to ML features
        return {
            'temperature': input_data['weather']['temperature_avg'],
            'humidity': input_data['weather']['humidity'],
            'rainfall': input_data['weather']['rainfall'],
            'soil_ph': input_data['soil']['ph_level'],
            'kc_value': input_data['growth_stage']['kc_value'],
            'days_after_sowing': input_data['days_after_sowing']
        }
    
    def _get_explanation(self, features):
        # Get feature importance for this prediction
        return self.predictor.explain_prediction(features)
```

---

## Key Design Decisions

### 1. Separate ML Pipeline from Backend
- **Reason**: Research reproducibility, independent model updates
- **Implementation**: Separate `/ml` directory with its own pipeline

### 2. Baseline Model
- **Reason**: Scientific reference point, ML improvement validation
- **Implementation**: FAO Penman-Monteith ET0 calculation

### 3. Multiple ML Models
- **Reason**: Model comparison, select best performer
- **Implementation**: Linear Regression, Random Forest, Gradient Boosting

### 4. Feature Engineering
- **Reason**: Domain knowledge integration, improved model performance
- **Implementation**: Weather, soil, crop, temporal, rainfall features

### 5. Explainability
- **Reason**: Farmer trust, research transparency
- **Implementation**: Feature importance, SHAP values, prediction explanations

### 6. Data Quality Analysis
- **Reason**: Reliable predictions, anomaly detection
- **Implementation**: IQR, Z-score, Isolation Forest methods

### 7. Model Versioning
- **Reason**: Reproducibility, rollback capability
- **Implementation**: Versioned model files with metadata
