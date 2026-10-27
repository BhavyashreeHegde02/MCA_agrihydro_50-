# API Architecture Design
## Smart Crop Water Requirement Prediction System

---

## API Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      API Gateway Layer                       │
│  (Rate Limiting, CORS, Authentication, Logging)            │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Application                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              API Versioning (/api/v1/)                 │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │   Auth   │  │  Farmer  │  │   Farm   │  │   Crop   │   │
│  │  Module  │  │  Module  │  │  Module  │  │  Module  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Weather │  │   Soil   │  │ Predict  │  │Irrigation│   │
│  │  Module  │  │  Module  │  │  Module  │  │  Module  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ WaterUse │  │Analytics │  │Advisory  │  │DataQuality│   │
│  │  Module  │  │  Module  │  │  Module  │  │  Module  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                   Admin Module                        │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                    Service Layer                            │
│  (Business Logic, Data Processing, ML Orchestration)       │
└─────────────────────────────────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                    Data Layer                               │
│  (PostgreSQL, External APIs, ML Models)                     │
└─────────────────────────────────────────────────────────────┘
```

---

## API Design Principles

### RESTful Design
- Resource-oriented URLs
- HTTP methods for operations (GET, POST, PUT, PATCH, DELETE)
- Standard HTTP status codes
- JSON request/response format

### Authentication
- JWT-based authentication
- Bearer token in Authorization header
- Token refresh mechanism
- Role-based access control

### Error Handling
- Consistent error response format
- Detailed error messages
- HTTP status codes for different error types
- Validation error details

### Rate Limiting
- Per-endpoint rate limits
- Per-user rate limits
- Burst allowance
- Retry-After header

### Versioning
- URL-based versioning (/api/v1/)
- Backward compatibility
- Deprecation headers

---

## API Endpoints

### Base URL
```
Production: https://api.cropwater-prediction.com/api/v1
Development: http://localhost:8000/api/v1
```

---

## 1. Authentication Module

### 1.1 Register Farmer
```http
POST /auth/register
Content-Type: application/json

Request Body:
{
  "email": "farmer@example.com",
  "password": "securePassword123",
  "full_name": "Ramesh Kumar",
  "phone": "+919876543210",
  "state": "Karnataka",
  "district": "Bangalore Rural",
  "taluk": "Dodballapur"
}

Response (201):
{
  "id": 1,
  "email": "farmer@example.com",
  "full_name": "Ramesh Kumar",
  "phone": "+919876543210",
  "state": "Karnataka",
  "district": "Bangalore Rural",
  "created_at": "2024-01-15T10:30:00Z"
}

Error (400):
{
  "error": "VALIDATION_ERROR",
  "message": "Email already registered",
  "details": {
    "field": "email",
    "constraint": "unique"
  }
}
```

### 1.2 Login
```http
POST /auth/login
Content-Type: application/json

Request Body:
{
  "email": "farmer@example.com",
  "password": "securePassword123"
}

Response (200):
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": 1,
    "email": "farmer@example.com",
    "full_name": "Ramesh Kumar"
  }
}

Error (401):
{
  "error": "INVALID_CREDENTIALS",
  "message": "Invalid email or password"
}
```

### 1.3 Refresh Token
```http
POST /auth/refresh
Content-Type: application/json

Request Body:
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}

Response (200):
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### 1.4 Logout
```http
POST /auth/logout
Authorization: Bearer {access_token}

Response (200):
{
  "message": "Successfully logged out"
}
```

---

## 2. Farmer Module

### 2.1 Get Farmer Profile
```http
GET /farmers/profile
Authorization: Bearer {access_token}

Response (200):
{
  "id": 1,
  "user_id": 1,
  "full_name": "Ramesh Kumar",
  "phone": "+919876543210",
  "state": "Karnataka",
  "district": "Bangalore Rural",
  "taluk": "Dodballapur",
  "address": "Village Road, Dodballapur",
  "created_at": "2024-01-15T10:30:00Z"
}
```

### 2.2 Update Farmer Profile
```http
PUT /farmers/profile
Authorization: Bearer {access_token}
Content-Type: application/json

Request Body:
{
  "phone": "+919876543211",
  "address": "New Address, Dodballapur"
}

Response (200):
{
  "id": 1,
  "full_name": "Ramesh Kumar",
  "phone": "+919876543211",
  "state": "Karnataka",
  "district": "Bangalore Rural",
  "updated_at": "2024-01-20T14:30:00Z"
}
```

---

## 3. Farm Module

### 3.1 List Farms
```http
GET /farms
Authorization: Bearer {access_token}

Query Parameters:
- page: int (default: 1)
- limit: int (default: 20)
- state: string (optional)
- district: string (optional)

Response (200):
{
  "farms": [
    {
      "id": 1,
      "name": "Main Field",
      "state": "Karnataka",
      "district": "Bangalore Rural",
      "total_area": 5.0,
      "area_unit": "acres",
      "latitude": 13.1234,
      "longitude": 77.5678,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "limit": 20
}
```

### 3.2 Create Farm
```http
POST /farms
Authorization: Bearer {access_token}
Content-Type: application/json

Request Body:
{
  "name": "Main Field",
  "state": "Karnataka",
  "district": "Bangalore Rural",
  "taluk": "Dodballapur",
  "latitude": 13.1234,
  "longitude": 77.5678,
  "total_area": 5.0,
  "area_unit": "acres"
}

Response (201):
{
  "id": 1,
  "farmer_id": 1,
  "name": "Main Field",
  "state": "Karnataka",
  "district": "Bangalore Rural",
  "total_area": 5.0,
  "area_unit": "acres",
  "created_at": "2024-01-15T10:30:00Z"
}
```

### 3.3 Get Farm Details
```http
GET /farms/{farm_id}
Authorization: Bearer {access_token}

Response (200):
{
  "id": 1,
  "name": "Main Field",
  "state": "Karnataka",
  "district": "Bangalore Rural",
  "total_area": 5.0,
  "area_unit": "acres",
  "latitude": 13.1234,
  "longitude": 77.5678,
  "fields": [
    {
      "id": 1,
      "name": "Field 1",
      "area": 2.0,
      "soil_type": "Clay Loam",
      "irrigation_method": "Drip"
    }
  ],
  "created_at": "2024-01-15T10:30:00Z"
}
```

### 3.4 Update Farm
```http
PUT /farms/{farm_id}
Authorization: Bearer {access_token}
Content-Type: application/json

Request Body:
{
  "name": "Updated Farm Name",
  "total_area": 6.0
}

Response (200):
{
  "id": 1,
  "name": "Updated Farm Name",
  "total_area": 6.0,
  "updated_at": "2024-01-20T14:30:00Z"
}
```

### 3.5 Delete Farm
```http
DELETE /farms/{farm_id}
Authorization: Bearer {access_token}

Response (200):
{
  "message": "Farm deleted successfully"
}
```

---

## 4. Field Module

### 4.1 Create Field
```http
POST /farms/{farm_id}/fields
Authorization: Bearer {access_token}
Content-Type: application/json

Request Body:
{
  "name": "Field 1",
  "area": 2.0,
  "area_unit": "acres",
  "soil_type": "Clay Loam",
  "irrigation_method": "Drip",
  "irrigation_efficiency": 0.85
}

Response (201):
{
  "id": 1,
  "farm_id": 1,
  "name": "Field 1",
  "area": 2.0,
  "soil_type": "Clay Loam",
  "irrigation_method": "Drip",
  "irrigation_efficiency": 0.85,
  "created_at": "2024-01-15T10:30:00Z"
}
```

### 4.2 Update Field
```http
PUT /fields/{field_id}
Authorization: Bearer {access_token}
Content-Type: application/json

Request Body:
{
  "irrigation_efficiency": 0.90
}

Response (200):
{
  "id": 1,
  "irrigation_efficiency": 0.90,
  "updated_at": "2024-01-20T14:30:00Z"
}
```

---

## 5. Crop Module

### 5.1 List Crops
```http
GET /crops
Authorization: Bearer {access_token}

Query Parameters:
- state: string (optional)
- category: string (optional)
- season: string (optional)

Response (200):
{
  "crops": [
    {
      "id": 1,
      "name": "Paddy",
      "scientific_name": "Oryza sativa",
      "category": "Cereal",
      "growing_season": "Kharif",
      "duration_days": 120
    },
    {
      "id": 2,
      "name": "Ragi",
      "scientific_name": "Eleusine coracana",
      "category": "Cereal",
      "growing_season": "Kharif",
      "duration_days": 105
    }
  ]
}
```

### 5.2 Get Crop Details
```http
GET /crops/{crop_id}
Authorization: Bearer {access_token}

Response (200):
{
  "id": 1,
  "name": "Paddy",
  "scientific_name": "Oryza sativa",
  "category": "Cereal",
  "growing_season": "Kharif",
  "duration_days": 120,
  "varieties": [
    {
      "id": 1,
      "name": "IR64",
      "description": "High yield variety"
    }
  ],
  "growth_stages": [
    {
      "id": 1,
      "stage_name": "Initial",
      "stage_order": 1,
      "duration_days": 20,
      "kc_value": 1.05
    }
  ]
}
```

### 5.3 Get Crop Growth Stages
```http
GET /crops/{crop_id}/growth-stages
Authorization: Bearer {access_token}

Response (200):
{
  "growth_stages": [
    {
      "id": 1,
      "crop_id": 1,
      "stage_name": "Initial/Establishment",
      "stage_order": 1,
      "duration_days": 20,
      "kc_value": 1.05,
      "description": "Seedling establishment phase"
    },
    {
      "id": 2,
      "crop_id": 1,
      "stage_name": "Development/Tillering",
      "stage_order": 2,
      "duration_days": 30,
      "kc_value": 1.20,
      "description": "Tillering and vegetative growth"
    }
  ]
}
```

### 5.4 Plant Crop in Field
```http
POST /fields/{field_id}/crops
Authorization: Bearer {access_token}
Content-Type: application/json

Request Body:
{
  "crop_id": 1,
  "variety_id": 1,
  "sowing_date": "2024-06-15",
  "planting_area": 2.0
}

Response (201):
{
  "id": 1,
  "field_id": 1,
  "crop_id": 1,
  "variety_id": 1,
  "sowing_date": "2024-06-15",
  "current_stage_id": 1,
  "planting_area": 2.0,
  "status": "active",
  "created_at": "2024-06-15T10:30:00Z"
}
```

---

## 6. Soil Module

### 6.1 Get District Soil Information
```http
GET /soil/district/{state}/{district}
Authorization: Bearer {access_token}

Response (200):
{
  "state": "Karnataka",
  "district": "Bangalore Rural",
  "dominant_soil_type": "Red Sandy Loam",
  "ph_avg": 6.5,
  "nitrogen_avg": 280.0,
  "phosphorus_avg": 45.0,
  "potassium_avg": 210.0
}
```

### 6.2 Add Soil Data for Field
```http
POST /fields/{field_id}/soil-data
Authorization: Bearer {access_token}
Content-Type: application/json

Request Body:
{
  "sample_date": "2024-06-01",
  "ph_level": 6.5,
  "nitrogen": 280.0,
  "phosphorus": 45.0,
  "potassium": 210.0,
  "soil_moisture": 25.5,
  "electrical_conductivity": 0.8,
  "organic_matter": 1.2,
  "texture": "Clay Loam"
}

Response (201):
{
  "id": 1,
  "field_id": 1,
  "sample_date": "2024-06-01",
  "ph_level": 6.5,
  "nitrogen": 280.0,
  "phosphorus": 45.0,
  "potassium": 210.0,
  "created_at": "2024-06-01T10:30:00Z"
}
```

### 6.3 Get Field Soil Data
```http
GET /fields/{field_id}/soil-data
Authorization: Bearer {access_token}

Response (200):
{
  "soil_data": [
    {
      "id": 1,
      "sample_date": "2024-06-01",
      "ph_level": 6.5,
      "nitrogen": 280.0,
      "phosphorus": 45.0,
      "potassium": 210.0,
      "soil_moisture": 25.5
    }
  ]
}
```

---

## 7. Weather Module

### 7.1 Get Current Weather
```http
GET /weather/current
Authorization: Bearer {access_token}

Query Parameters:
- district: string (required)
- lat: float (optional)
- lon: float (optional)

Response (200):
{
  "district": "Bangalore Rural",
  "date": "2024-06-20",
  "temperature_max": 32.5,
  "temperature_min": 24.0,
  "temperature_avg": 28.2,
  "humidity": 65.0,
  "wind_speed": 12.5,
  "rainfall": 0.0,
  "solar_radiation": 18.5,
  "et0": 5.8,
  "data_source": "api"
}
```

### 7.2 Get Weather Forecast
```http
GET /weather/forecast
Authorization: Bearer {access_token}

Query Parameters:
- district: string (required)
- days: int (default: 7)

Response (200):
{
  "district": "Bangalore Rural",
  "forecast": [
    {
      "date": "2024-06-21",
      "temperature_max": 33.0,
      "temperature_min": 24.5,
      "humidity": 60.0,
      "wind_speed": 10.0,
      "rainfall": 5.0,
      "rainfall_probability": 40
    },
    {
      "date": "2024-06-22",
      "temperature_max": 31.5,
      "temperature_min": 23.0,
      "humidity": 70.0,
      "wind_speed": 8.0,
      "rainfall": 15.0,
      "rainfall_probability": 80
    }
  ]
}
```

### 7.3 Get Historical Weather
```http
GET /weather/historical
Authorization: Bearer {access_token}

Query Parameters:
- district: string (required)
- start_date: string (required, YYYY-MM-DD)
- end_date: string (required, YYYY-MM-DD)

Response (200):
{
  "district": "Bangalore Rural",
  "start_date": "2024-01-01",
  "end_date": "2024-06-20",
  "weather_data": [
    {
      "date": "2024-06-01",
      "temperature_avg": 28.5,
      "rainfall": 2.5,
      "humidity": 62.0
    }
  ]
}
```

---

## 8. Prediction Module (Core)

### 8.1 Predict CWR
```http
POST /predictions/cwr
Authorization: Bearer {access_token}
Content-Type: application/json

Request Body:
{
  "field_crop_id": 1,
  "prediction_date": "2024-06-20",
  "use_current_weather": true,
  "override_soil_data": {
    "ph_level": 6.5,
    "nitrogen": 280.0,
    "phosphorus": 45.0,
    "potassium": 210.0
  }
}

Response (200):
{
  "id": 1,
  "field_crop_id": 1,
  "prediction_date": "2024-06-20",
  "crop": {
    "id": 1,
    "name": "Paddy"
  },
  "growth_stage": {
    "id": 2,
    "stage_name": "Development/Tillering",
    "kc_value": 1.20
  },
  "cwr_mm_day": 5.8,
  "cwr_mm_week": 40.6,
  "effective_rainfall": 12.5,
  "irrigation_requirement": 28.1,
  "weather_data": {
    "temperature_avg": 28.2,
    "humidity": 65.0,
    "rainfall": 0.0
  },
  "soil_data": {
    "ph_level": 6.5,
    "soil_type": "Clay Loam"
  },
  "prediction_confidence": 0.85,
  "model_version": "CWR_Model_v1.0",
  "created_at": "2024-06-20T10:30:00Z"
}

Error (400):
{
  "error": "INVALID_INPUT",
  "message": "Weather data unavailable for the specified district"
}
```

### 8.2 Get Prediction History
```http
GET /predictions/history
Authorization: Bearer {access_token}

Query Parameters:
- field_crop_id: int (optional)
- start_date: string (optional)
- end_date: string (optional)
- page: int (default: 1)
- limit: int (default: 20)

Response (200):
{
  "predictions": [
    {
      "id": 1,
      "prediction_date": "2024-06-20",
      "crop_name": "Paddy",
      "growth_stage": "Development/Tillering",
      "cwr_mm_day": 5.8,
      "irrigation_requirement": 28.1,
      "created_at": "2024-06-20T10:30:00Z"
    }
  ],
  "total": 50,
  "page": 1,
  "limit": 20
}
```

### 8.3 Get Prediction Details
```http
GET /predictions/{prediction_id}
Authorization: Bearer {access_token}

Response (200):
{
  "id": 1,
  "field_crop_id": 1,
  "prediction_date": "2024-06-20",
  "crop": {
    "id": 1,
    "name": "Paddy"
  },
  "growth_stage": {
    "id": 2,
    "stage_name": "Development/Tillering",
    "kc_value": 1.20
  },
  "cwr_mm_day": 5.8,
  "cwr_mm_week": 40.6,
  "effective_rainfall": 12.5,
  "irrigation_requirement": 28.1,
  "weather_data": {
    "temperature_avg": 28.2,
    "humidity": 65.0,
    "rainfall": 0.0,
    "wind_speed": 12.5,
    "solar_radiation": 18.5
  },
  "soil_data": {
    "ph_level": 6.5,
    "nitrogen": 280.0,
    "phosphorus": 45.0,
    "potassium": 210.0,
    "soil_type": "Clay Loam"
  },
  "features": {
    "temperature": 28.2,
    "humidity": 65.0,
    "kc_value": 1.20,
    "days_after_sowing": 35
  },
  "prediction_confidence": 0.85,
  "model_version": "CWR_Model_v1.0",
  "created_at": "2024-06-20T10:30:00Z"
}
```

### 8.4 Get Prediction Explanation
```http
GET /predictions/{prediction_id}/explanation
Authorization: Bearer {access_token}

Response (200):
{
  "prediction_id": 1,
  "feature_importance": [
    {
      "feature": "temperature",
      "importance": 0.35,
      "direction": "positive",
      "description": "Higher temperature increased water requirement"
    },
    {
      "feature": "growth_stage",
      "importance": 0.28,
      "direction": "positive",
      "description": "Mid-season stage requires more water"
    },
    {
      "feature": "rainfall",
      "importance": 0.20,
      "direction": "negative",
      "description": "Recent rainfall reduced irrigation requirement"
    },
    {
      "feature": "humidity",
      "importance": 0.12,
      "direction": "negative",
      "description": "Higher humidity reduced evapotranspiration"
    },
    {
      "feature": "soil_moisture",
      "importance": 0.05,
      "direction": "negative",
      "description": "Soil moisture contributed to reduced requirement"
    }
  ],
  "baseline_comparison": {
    "baseline_cwr": 6.2,
    "ml_cwr": 5.8,
    "difference": -0.4,
    "improvement": "6.5% reduction"
  }
}
```

---

## 9. Irrigation Module

### 9.1 Calculate Irrigation Requirement
```http
POST /irrigation/calculate
Authorization: Bearer {access_token}
Content-Type: application/json

Request Body:
{
  "prediction_id": 1,
  "irrigation_efficiency": 0.85,
  "forecast_rainfall": 15.0
}

Response (200):
{
  "prediction_id": 1,
  "cwr_mm_day": 5.8,
  "cwr_mm_week": 40.6,
  "effective_rainfall": 12.5,
  "forecast_rainfall": 15.0,
  "irrigation_efficiency": 0.85,
  "irrigation_requirement_mm_week": 28.1,
  "irrigation_requirement_liters_acre": 281000,
  "recommended_frequency": "Every 3 days",
  "next_irrigation_date": "2024-06-23",
  "assumptions": [
    "Irrigation efficiency of 85%",
    "Forecast rainfall considered",
    "Soil moisture at field capacity"
  ]
}
```

### 9.2 Record Irrigation Event
```http
POST /irrigation/records
Authorization: Bearer {access_token}
Content-Type: application/json

Request Body:
{
  "field_crop_id": 1,
  "irrigation_date": "2024-06-20",
  "method": "Drip",
  "duration_hours": 2.5,
  "water_applied_mm": 30.0,
  "efficiency": 0.85,
  "notes": "Morning irrigation"
}

Response (201):
{
  "id": 1,
  "field_crop_id": 1,
  "irrigation_date": "2024-06-20",
  "method": "Drip",
  "duration_hours": 2.5,
  "water_applied_mm": 30.0,
  "efficiency": 0.85,
  "created_at": "2024-06-20T10:30:00Z"
}
```

### 9.3 Get Irrigation History
```http
GET /irrigation/records
Authorization: Bearer {access_token}

Query Parameters:
- field_crop_id: int (optional)
- start_date: string (optional)
- end_date: string (optional)

Response (200):
{
  "records": [
    {
      "id": 1,
      "irrigation_date": "2024-06-20",
      "method": "Drip",
      "water_applied_mm": 30.0,
      "efficiency": 0.85
    }
  ]
}
```

---

## 10. Water Use Module

### 10.1 Record Water Use
```http
POST /water-use
Authorization: Bearer {access_token}
Content-Type: application/json

Request Body:
{
  "field_crop_id": 1,
  "record_date": "2024-06-20",
  "water_used_mm": 30.0,
  "water_source": "Borewell",
  "area_irrigated": 2.0,
  "estimated_cost": 150.0
}

Response (201):
{
  "id": 1,
  "field_crop_id": 1,
  "record_date": "2024-06-20",
  "water_used_mm": 30.0,
  "water_source": "Borewell",
  "area_irrigated": 2.0,
  "estimated_cost": 150.0,
  "created_at": "2024-06-20T10:30:00Z"
}
```

### 10.2 Get Water Use History
```http
GET /water-use
Authorization: Bearer {access_token}

Query Parameters:
- field_crop_id: int (optional)
- start_date: string (optional)
- end_date: string (optional)

Response (200):
{
  "water_use": [
    {
      "id": 1,
      "record_date": "2024-06-20",
      "water_used_mm": 30.0,
      "water_source": "Borewell",
      "estimated_cost": 150.0
    }
  ],
  "summary": {
    "total_water_used_mm": 450.0,
    "total_cost": 2250.0,
    "average_daily_use": 15.0
  }
}
```

---

## 11. Analytics Module

### 11.1 Get CWR Analytics
```http
GET /analytics/cwr
Authorization: Bearer {access_token}

Query Parameters:
- field_crop_id: int (required)
- start_date: string (required)
- end_date: string (required)

Response (200):
{
  "field_crop_id": 1,
  "start_date": "2024-06-01",
  "end_date": "2024-06-20",
  "cwr_trend": [
    {
      "date": "2024-06-01",
      "cwr_mm_day": 4.5
    },
    {
      "date": "2024-06-10",
      "cwr_mm_day": 5.2
    },
    {
      "date": "2024-06-20",
      "cwr_mm_day": 5.8
    }
  ],
  "statistics": {
    "avg_cwr_mm_day": 5.1,
    "max_cwr_mm_day": 5.8,
    "min_cwr_mm_day": 4.5,
    "total_cwr_mm": 102.0
  }
}
```

### 11.2 Get Water Use Analytics
```http
GET /analytics/water-use
Authorization: Bearer {access_token}

Query Parameters:
- field_crop_id: int (required)
- start_date: string (required)
- end_date: string (required)

Response (200):
{
  "field_crop_id": 1,
  "start_date": "2024-06-01",
  "end_date": "2024-06-20",
  "predicted_vs_actual": [
    {
      "date": "2024-06-01",
      "predicted_mm": 4.5,
      "actual_mm": 5.0,
      "difference": 0.5
    }
  ],
  "summary": {
    "total_predicted_mm": 102.0,
    "total_actual_mm": 110.0,
    "efficiency_percentage": 92.7,
    "water_saved_mm": -8.0
  }
}
```

### 11.3 Get Rainfall vs CWR Analysis
```http
GET /analytics/rainfall-cwr
Authorization: Bearer {access_token}

Query Parameters:
- district: string (required)
- start_date: string (required)
- end_date: string (required)

Response (200):
{
  "district": "Bangalore Rural",
  "start_date": "2024-06-01",
  "end_date": "2024-06-20",
  "data": [
    {
      "date": "2024-06-01",
      "rainfall_mm": 5.0,
      "cwr_mm_day": 4.5,
      "effective_rainfall": 4.0
    }
  ],
  "correlation": {
    "coefficient": -0.65,
    "interpretation": "Moderate negative correlation"
  }
}
```

---

## 12. Advisory Module

### 12.1 Get Advisory
```http
GET /advisory
Authorization: Bearer {access_token}

Query Parameters:
- prediction_id: int (required)

Response (200):
{
  "prediction_id": 1,
  "advisories": [
    {
      "id": 1,
      "advisory_type": "IRRIGATION",
      "message": "Crop water requirement is currently high due to elevated temperature and mid-season growth stage. Consider irrigation within the next 2-3 days.",
      "priority": "high",
      "action_required": true
    },
    {
      "id": 2,
      "advisory_type": "RAINFALL",
      "message": "Expected rainfall in the next 3 days may reduce irrigation requirement by approximately 15mm.",
      "priority": "medium",
      "action_required": false
    }
  ]
}
```

---

## 13. Data Quality Module

### 13.1 Get Data Quality Alerts
```http
GET /data-quality/anomalies
Authorization: Bearer {access_token}

Query Parameters:
- prediction_id: int (optional)
- severity: string (optional)
- start_date: string (optional)
- end_date: string (optional)

Response (200):
{
  "alerts": [
    {
      "id": 1,
      "prediction_id": 1,
      "alert_type": "RAINFALL_ANOMALY",
      "severity": "warning",
      "description": "Rainfall value is unusually high compared with historical observations for this district",
      "detected_value": 85.0,
      "expected_range": {
        "min": 0.0,
        "max": 30.0,
        "mean": 8.5
      },
      "created_at": "2024-06-20T10:30:00Z"
    }
  ]
}
```

### 13.2 Get Data Quality Summary
```http
GET /data-quality/summary
Authorization: Bearer {access_token}

Query Parameters:
- district: string (required)
- date: string (required)

Response (200):
{
  "district": "Bangalore Rural",
  "date": "2024-06-20",
  "overall_status": "normal",
  "checks": {
    "weather_data": {
      "status": "valid",
      "completeness": 100
    },
    "soil_data": {
      "status": "valid",
      "completeness": 85
    },
    "rainfall_data": {
      "status": "warning",
      "completeness": 100,
      "anomaly_detected": true
    }
  }
}
```

---

## 14. Admin Module (Research Dashboard)

### 14.1 Get Model Performance
```http
GET /admin/model-performance
Authorization: Bearer {access_token} (Admin role required)

Response (200):
{
  "models": [
    {
      "model_name": "Random Forest",
      "version": "v1.0",
      "mae": 0.45,
      "rmse": 0.62,
      "r2_score": 0.87,
      "mape": 8.5,
      "training_date": "2024-01-15"
    },
    {
      "model_name": "Gradient Boosting",
      "version": "v1.0",
      "mae": 0.38,
      "rmse": 0.55,
      "r2_score": 0.91,
      "mape": 7.2,
      "training_date": "2024-01-15"
    }
  ],
  "best_model": {
    "name": "Gradient Boosting",
    "version": "v1.0",
    "reason": "Lowest MAE and highest R² score"
  }
}
```

### 14.2 Get Dataset Statistics
```http
GET /admin/dataset-statistics
Authorization: Bearer {access_token} (Admin role required)

Response (200):
{
  "datasets": {
    "crop_data": {
      "total_records": 150,
      "missing_values": 0,
      "date_range": "2020-01-01 to 2024-06-20"
    },
    "soil_data": {
      "total_records": 500,
      "missing_values": 25,
      "date_range": "2020-01-01 to 2024-06-20"
    },
    "weather_data": {
      "total_records": 10000,
      "missing_values": 150,
      "date_range": "2020-01-01 to 2024-06-20"
    }
  },
  "overall_quality": 98.5
}
```

### 14.3 Get Prediction Statistics
```http
GET /admin/prediction-statistics
Authorization: Bearer {access_token} (Admin role required)

Query Parameters:
- start_date: string (optional)
- end_date: string (optional)

Response (200):
{
  "start_date": "2024-06-01",
  "end_date": "2024-06-20",
  "total_predictions": 1250,
  "predictions_by_crop": [
    {
      "crop": "Paddy",
      "count": 500
    },
    {
      "crop": "Ragi",
      "count": 300
    }
  ],
  "predictions_by_district": [
    {
      "district": "Bangalore Rural",
      "count": 450
    }
  ],
  "average_confidence": 0.82
}
```

---

## Standard Error Response Format

```json
{
  "error": "ERROR_CODE",
  "message": "Human-readable error message",
  "details": {
    "field": "field_name",
    "constraint": "constraint_description"
  },
  "timestamp": "2024-06-20T10:30:00Z"
}
```

### Common Error Codes

- `VALIDATION_ERROR`: Input validation failed
- `UNAUTHORIZED`: Authentication required or failed
- `FORBIDDEN`: Insufficient permissions
- `NOT_FOUND`: Resource not found
- `CONFLICT`: Resource conflict (e.g., duplicate)
- `INTERNAL_ERROR`: Server error
- `SERVICE_UNAVAILABLE`: External service unavailable
- `RATE_LIMIT_EXCEEDED`: Rate limit exceeded

---

## Rate Limiting

### Default Limits
- Authentication endpoints: 10 requests/minute
- Prediction endpoints: 30 requests/minute
- Data endpoints: 60 requests/minute
- Admin endpoints: 20 requests/minute

### Rate Limit Response Headers
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1718894400
```

---

## Pagination

### Standard Pagination Parameters
- `page`: Page number (default: 1)
- `limit`: Items per page (default: 20, max: 100)

### Pagination Response
```json
{
  "data": [...],
  "total": 150,
  "page": 1,
  "limit": 20,
  "pages": 8
}
```

---

## API Security

### Authentication
- All endpoints (except auth) require JWT token
- Token in `Authorization: Bearer {token}` header
- Token expiration: 1 hour (access), 7 days (refresh)

### CORS
- Allowed origins: Configured per environment
- Allowed methods: GET, POST, PUT, PATCH, DELETE
- Allowed headers: Authorization, Content-Type

### Input Validation
- All inputs validated using Pydantic schemas
- SQL injection prevention via parameterized queries
- XSS prevention via proper escaping

---

## API Versioning Strategy

### Current Version: v1
- Base path: `/api/v1/`
- Stable endpoints
- Backward compatible changes only

### Future Versions
- New versions as `/api/v2/`
- Deprecation headers for old versions
- Minimum 6 months deprecation notice
