# Database Schema Design
## Smart Crop Water Requirement Prediction System

---

## Entity Relationship Diagram (ERD)

```
┌─────────────────┐       ┌─────────────────┐
│      users      │       │    farmers      │
├─────────────────┤       ├─────────────────┤
│ id (PK)         │──┐    │ id (PK)         │
│ email           │  │    │ user_id (FK)     │
│ password_hash   │  └───→│ full_name        │
│ full_name       │       │ phone           │
│ phone           │       │ state           │
│ is_active       │       │ district        │
│ created_at      │       │ taluk           │
│ updated_at      │       │ address         │
└─────────────────┘       │ created_at      │
                          │ updated_at      │
                          └─────────────────┘
                                   │
                                   │ 1
                                   │
                                   │ N
                                   ↓
                          ┌─────────────────┐
                          │      farms      │
                          ├─────────────────┤
                          │ id (PK)         │
                          │ farmer_id (FK)  │←──┐
                          │ name            │   │
                          │ state           │   │
                          │ district        │   │
                          │ taluk           │   │
                          │ latitude        │   │
                          │ longitude       │   │
                          │ total_area      │   │
                          │ area_unit       │   │
                          │ created_at      │   │
                          │ updated_at      │   │
                          └─────────────────┘   │
                                   │ 1           │
                                   │             │ N
                                   │ N           │
                                   ↓             │
                          ┌─────────────────┐   │
                          │     fields      │   │
                          ├─────────────────┤   │
                          │ id (PK)         │   │
                          │ farm_id (FK)    │───┘
                          │ name            │
                          │ area            │
                          │ area_unit       │
                          │ soil_type       │
                          │ irrigation_method│
                          │ irrigation_efficiency│
                          │ created_at      │
                          │ updated_at      │
                          └─────────────────┘
                                   │
                                   │ 1
                                   │
                                   │ N
                                   ↓
                          ┌─────────────────┐
                          │   field_crops   │
                          ├─────────────────┤
                          │ id (PK)         │
                          │ field_id (FK)   │←──┐
                          │ crop_id (FK)    │   │
                          │ variety_id (FK) │   │
                          │ sowing_date     │   │
                          │ current_stage_id│  │
                          │ planting_area   │   │
                          │ status          │   │
                          │ created_at      │   │
                          │ updated_at      │   │
                          └─────────────────┘   │
                                   │ 1           │
                                   │             │ N
                                   │ N           │
                                   ↓             │
                          ┌─────────────────┐   │
                          │   predictions   │   │
                          ├─────────────────┤   │
                          │ id (PK)         │   │
                          │ field_crop_id (FK)│←─┘
                          │ prediction_date │
                          │ model_version_id │
                          │ cwr_mm_day      │
                          │ cwr_mm_week     │
                          │ effective_rainfall│
                          │ irrigation_requirement│
                          │ weather_data (JSONB)│
                          │ soil_data (JSONB)   │
                          │ features (JSONB)     │
                          │ prediction_confidence│
                          │ created_at      │
                          └─────────────────┘

┌─────────────────┐       ┌─────────────────┐
│      crops      │       │crop_varieties   │
├─────────────────┤       ├─────────────────┤
│ id (PK)         │──┐    │ id (PK)         │
│ name            │  │    │ crop_id (FK)    │←──┐
│ scientific_name │  └───→│ name            │   │
│ category        │       │ description     │   │
│ growing_season  │       │ characteristics │   │
│ duration_days   │       │ created_at      │   │
│ created_at      │       └─────────────────┘   │
└─────────────────┘                            │
                                               │ N
                                               │
                                               │ 1
                                               ↓
                                    ┌─────────────────┐
                                    │crop_growth_stages│
                                    ├─────────────────┤
                                    │ id (PK)         │
                                    │ crop_id (FK)    │
                                    │ stage_name      │
                                    │ stage_order     │
                                    │ duration_days   │
                                    │ kc_value        │
                                    │ description     │
                                    │ created_at      │
                                    └─────────────────┘

┌─────────────────┐       ┌─────────────────┐
│   soil_data     │       │district_soil_map│
├─────────────────┤       ├─────────────────┤
│ id (PK)         │       │ id (PK)         │
│ field_id (FK)   │←──┐    │ state           │
│ sample_date     │   │    │ district        │
│ ph_level        │   │    │ dominant_soil_type│
│ nitrogen        │   │    │ ph_avg          │
│ phosphorus      │   │    │ nitrogen_avg    │
│ potassium       │   │    │ phosphorus_avg  │
│ soil_moisture   │   │    │ potassium_avg   │
│ electrical_conductivity│ │ created_at      │
│ organic_matter  │   │    └─────────────────┘
│ texture         │   │
│ created_at      │   │
└─────────────────┘   │
                       │
                       │ N
                       │
                       │ 1
                       ↓
            ┌─────────────────┐
            │ weather_data    │
            ├─────────────────┤
            │ id (PK)         │
            │ district        │
            │ date            │
            │ temperature_max │
            │ temperature_min │
            │ temperature_avg │
            │ humidity        │
            │ wind_speed      │
            │ rainfall        │
            │ solar_radiation │
            │ et0             │
            │ data_source     │
            │ created_at      │
            └─────────────────┘

┌─────────────────┐       ┌─────────────────┐
│ irrigation_records│     │  water_use      │
├─────────────────┤       ├─────────────────┤
│ id (PK)         │       │ id (PK)         │
│ field_crop_id (FK)│     │ field_crop_id (FK)│
│ irrigation_date │       │ record_date     │
│ method          │       │ water_used_mm   │
│ duration_hours  │       │ water_source    │
│ water_applied_mm│       │ area_irrigated  │
│ efficiency      │       │ estimated_cost  │
│ notes           │       │ created_at      │
│ created_at      │       └─────────────────┘
└─────────────────┘

┌─────────────────┐       ┌─────────────────┐
│ model_versions  │       │data_quality_alerts│
├─────────────────┤       ├─────────────────┤
│ id (PK)         │       │ id (PK)         │
│ model_name      │       │ prediction_id (FK)│
│ version         │       │ alert_type      │
│ algorithm       │       │ severity        │
│ training_date   │       │ description     │
│ dataset_version │       │ detected_value  │
│ features (JSONB)│       │ expected_range  │
│ mae             │       │ created_at      │
│ rmse            │       └─────────────────┘
│ r2_score        │
│ mape            │
│ is_active       │
│ created_at      │
└─────────────────┘

┌─────────────────┐
│   advisories    │
├─────────────────┤
│ id (PK)         │
│ prediction_id (FK)│
│ advisory_type   │
│ message         │
│ priority        │
│ action_required │
│ created_at      │
└─────────────────┘
```

---

## Detailed Table Schemas

### 1. users

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_is_active ON users(is_active);
```

### 2. farmers

```sql
CREATE TABLE farmers (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    full_name VARCHAR(255) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    state VARCHAR(100) NOT NULL,
    district VARCHAR(100) NOT NULL,
    taluk VARCHAR(100),
    address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id)
);

CREATE INDEX idx_farmers_user_id ON farmers(user_id);
CREATE INDEX idx_farmers_state_district ON farmers(state, district);
```

### 3. farms

```sql
CREATE TABLE farms (
    id SERIAL PRIMARY KEY,
    farmer_id INTEGER REFERENCES farmers(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    state VARCHAR(100) NOT NULL,
    district VARCHAR(100) NOT NULL,
    taluk VARCHAR(100),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    total_area DECIMAL(10, 2) NOT NULL,
    area_unit VARCHAR(20) DEFAULT 'acres',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_farms_farmer_id ON farms(farmer_id);
CREATE INDEX idx_farms_location ON farms(state, district);
```

### 4. fields

```sql
CREATE TABLE fields (
    id SERIAL PRIMARY KEY,
    farm_id INTEGER REFERENCES farms(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    area DECIMAL(10, 2) NOT NULL,
    area_unit VARCHAR(20) DEFAULT 'acres',
    soil_type VARCHAR(100),
    irrigation_method VARCHAR(100),
    irrigation_efficiency DECIMAL(5, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_fields_farm_id ON fields(farm_id);
```

### 5. crops

```sql
CREATE TABLE crops (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    scientific_name VARCHAR(255),
    category VARCHAR(100),
    growing_season VARCHAR(50),
    duration_days INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_crops_name ON crops(name);
```

### 6. crop_varieties

```sql
CREATE TABLE crop_varieties (
    id SERIAL PRIMARY KEY,
    crop_id INTEGER REFERENCES crops(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    characteristics JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_crop_varieties_crop_id ON crop_varieties(crop_id);
```

### 7. crop_growth_stages

```sql
CREATE TABLE crop_growth_stages (
    id SERIAL PRIMARY KEY,
    crop_id INTEGER REFERENCES crops(id) ON DELETE CASCADE,
    stage_name VARCHAR(255) NOT NULL,
    stage_order INTEGER NOT NULL,
    duration_days INTEGER,
    kc_value DECIMAL(5, 3),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(crop_id, stage_order)
);

CREATE INDEX idx_growth_stages_crop_id ON crop_growth_stages(crop_id);
```

### 8. field_crops

```sql
CREATE TABLE field_crops (
    id SERIAL PRIMARY KEY,
    field_id INTEGER REFERENCES fields(id) ON DELETE CASCADE,
    crop_id INTEGER REFERENCES crops(id),
    variety_id INTEGER REFERENCES crop_varieties(id),
    sowing_date DATE NOT NULL,
    current_stage_id INTEGER REFERENCES crop_growth_stages(id),
    planting_area DECIMAL(10, 2),
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_field_crops_field_id ON field_crops(field_id);
CREATE INDEX idx_field_crops_crop_id ON field_crops(crop_id);
CREATE INDEX idx_field_crops_sowing_date ON field_crops(sowing_date);
```

### 9. soil_data

```sql
CREATE TABLE soil_data (
    id SERIAL PRIMARY KEY,
    field_id INTEGER REFERENCES fields(id) ON DELETE CASCADE,
    sample_date DATE,
    ph_level DECIMAL(4, 2),
    nitrogen DECIMAL(10, 2),
    phosphorus DECIMAL(10, 2),
    potassium DECIMAL(10, 2),
    soil_moisture DECIMAL(5, 2),
    electrical_conductivity DECIMAL(10, 2),
    organic_matter DECIMAL(5, 2),
    texture VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_soil_data_field_id ON soil_data(field_id);
CREATE INDEX idx_soil_data_sample_date ON soil_data(sample_date);
```

### 10. district_soil_map

```sql
CREATE TABLE district_soil_map (
    id SERIAL PRIMARY KEY,
    state VARCHAR(100) NOT NULL,
    district VARCHAR(100) NOT NULL,
    dominant_soil_type VARCHAR(100),
    ph_avg DECIMAL(4, 2),
    nitrogen_avg DECIMAL(10, 2),
    phosphorus_avg DECIMAL(10, 2),
    potassium_avg DECIMAL(10, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(state, district)
);

CREATE INDEX idx_district_soil_map_location ON district_soil_map(state, district);
```

### 11. weather_data

```sql
CREATE TABLE weather_data (
    id SERIAL PRIMARY KEY,
    district VARCHAR(100) NOT NULL,
    date DATE NOT NULL,
    temperature_max DECIMAL(5, 2),
    temperature_min DECIMAL(5, 2),
    temperature_avg DECIMAL(5, 2),
    humidity DECIMAL(5, 2),
    wind_speed DECIMAL(5, 2),
    rainfall DECIMAL(10, 2),
    solar_radiation DECIMAL(10, 2),
    et0 DECIMAL(10, 2),
    data_source VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(district, date)
);

CREATE INDEX idx_weather_data_district_date ON weather_data(district, date);
CREATE INDEX idx_weather_data_date ON weather_data(date);
```

### 12. predictions

```sql
CREATE TABLE predictions (
    id SERIAL PRIMARY KEY,
    field_crop_id INTEGER REFERENCES field_crops(id) ON DELETE CASCADE,
    prediction_date DATE NOT NULL,
    model_version_id INTEGER REFERENCES model_versions(id),
    cwr_mm_day DECIMAL(10, 3),
    cwr_mm_week DECIMAL(10, 3),
    effective_rainfall DECIMAL(10, 2),
    irrigation_requirement DECIMAL(10, 2),
    weather_data JSONB,
    soil_data JSONB,
    features JSONB,
    prediction_confidence DECIMAL(5, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_predictions_field_crop_id ON predictions(field_crop_id);
CREATE INDEX idx_predictions_prediction_date ON predictions(prediction_date);
CREATE INDEX idx_predictions_model_version ON predictions(model_version_id);
```

### 13. irrigation_records

```sql
CREATE TABLE irrigation_records (
    id SERIAL PRIMARY KEY,
    field_crop_id INTEGER REFERENCES field_crops(id) ON DELETE CASCADE,
    irrigation_date DATE NOT NULL,
    method VARCHAR(100),
    duration_hours DECIMAL(5, 2),
    water_applied_mm DECIMAL(10, 2),
    efficiency DECIMAL(5, 2),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_irrigation_field_crop_id ON irrigation_records(field_crop_id);
CREATE INDEX idx_irrigation_date ON irrigation_records(irrigation_date);
```

### 14. water_use

```sql
CREATE TABLE water_use (
    id SERIAL PRIMARY KEY,
    field_crop_id INTEGER REFERENCES field_crops(id) ON DELETE CASCADE,
    record_date DATE NOT NULL,
    water_used_mm DECIMAL(10, 2),
    water_source VARCHAR(100),
    area_irrigated DECIMAL(10, 2),
    estimated_cost DECIMAL(10, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(field_crop_id, record_date)
);

CREATE INDEX idx_water_use_field_crop_id ON water_use(field_crop_id);
CREATE INDEX idx_water_use_record_date ON water_use(record_date);
```

### 15. model_versions

```sql
CREATE TABLE model_versions (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(255) NOT NULL,
    version VARCHAR(50) NOT NULL,
    algorithm VARCHAR(100) NOT NULL,
    training_date DATE NOT NULL,
    dataset_version VARCHAR(100),
    features JSONB,
    mae DECIMAL(10, 4),
    rmse DECIMAL(10, 4),
    r2_score DECIMAL(10, 4),
    mape DECIMAL(10, 4),
    is_active BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(model_name, version)
);

CREATE INDEX idx_model_versions_active ON model_versions(is_active);
CREATE INDEX idx_model_versions_name ON model_versions(model_name);
```

### 16. data_quality_alerts

```sql
CREATE TABLE data_quality_alerts (
    id SERIAL PRIMARY KEY,
    prediction_id INTEGER REFERENCES predictions(id) ON DELETE CASCADE,
    alert_type VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    description TEXT,
    detected_value DECIMAL(20, 4),
    expected_range JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_data_quality_prediction_id ON data_quality_alerts(prediction_id);
CREATE INDEX idx_data_quality_severity ON data_quality_alerts(severity);
```

### 17. advisories

```sql
CREATE TABLE advisories (
    id SERIAL PRIMARY KEY,
    prediction_id INTEGER REFERENCES predictions(id) ON DELETE CASCADE,
    advisory_type VARCHAR(100) NOT NULL,
    message TEXT NOT NULL,
    priority VARCHAR(20) DEFAULT 'medium',
    action_required BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_advisories_prediction_id ON advisories(prediction_id);
CREATE INDEX idx_advisories_priority ON advisories(priority);
```

---

## Relationships Summary

### One-to-One
- users ↔ farmers (1:1)

### One-to-Many
- farmers → farms (1:N)
- farms → fields (1:N)
- fields → field_crops (1:N)
- field_crops → predictions (1:N)
- field_crops → irrigation_records (1:N)
- field_crops → water_use (1:N)
- crops → crop_varieties (1:N)
- crops → crop_growth_stages (1:N)
- fields → soil_data (1:N)
- predictions → data_quality_alerts (1:N)
- predictions → advisories (1:N)

### Many-to-One
- field_crops → crops (N:1)
- field_crops → crop_varieties (N:1)
- field_crops → crop_growth_stages (N:1)
- predictions → model_versions (N:1)

---

## JSONB Fields Usage

### weather_data (in predictions)
```json
{
  "temperature_max": 35.5,
  "temperature_min": 24.2,
  "temperature_avg": 29.8,
  "humidity": 65.0,
  "wind_speed": 12.5,
  "rainfall": 5.2,
  "solar_radiation": 18.5,
  "et0": 6.2
}
```

### soil_data (in predictions)
```json
{
  "ph_level": 6.5,
  "nitrogen": 280.0,
  "phosphorus": 45.0,
  "potassium": 210.0,
  "soil_moisture": 25.5,
  "soil_type": "Clay Loam"
}
```

### features (in predictions)
```json
{
  "temperature": 29.8,
  "humidity": 65.0,
  "wind_speed": 12.5,
  "rainfall": 5.2,
  "soil_ph": 6.5,
  "nitrogen": 280.0,
  "phosphorus": 45.0,
  "potassium": 210.0,
  "kc_value": 1.1,
  "growth_stage_order": 3,
  "days_after_sowing": 45,
  "irrigation_efficiency": 0.75
}
```

### features (in model_versions)
```json
{
  "numerical": ["temperature", "humidity", "rainfall", "soil_ph"],
  "categorical": ["crop", "soil_type", "irrigation_method"],
  "engineered": ["effective_rainfall", "days_after_sowing", "kc_value"]
}
```

### expected_range (in data_quality_alerts)
```json
{
  "min": 0.0,
  "max": 50.0,
  "mean": 12.5,
  "std": 8.3
}
```

---

## Database Constraints & Indexes

### Foreign Key Constraints
All foreign key relationships have ON DELETE CASCADE where appropriate to maintain data integrity.

### Unique Constraints
- users.email
- farmers.user_id
- crop_growth_stages (crop_id, stage_order)
- weather_data (district, date)
- water_use (field_crop_id, record_date)
- model_versions (model_name, version)

### Indexes
Created on:
- All foreign key columns
- Frequently queried columns (email, dates, location)
- Composite indexes for common query patterns

---

## Data Retention Policy

### Short-term Data (1 year)
- weather_data
- data_quality_alerts
- advisories

### Medium-term Data (3 years)
- predictions
- irrigation_records
- water_use

### Long-term Data (7+ years)
- users, farmers, farms, fields
- crops, crop_varieties, crop_growth_stages
- model_versions

---

## Migration Strategy

Use Alembic for database migrations:
- Version-controlled schema changes
- Rollback capability
- Development/staging/production environment support
