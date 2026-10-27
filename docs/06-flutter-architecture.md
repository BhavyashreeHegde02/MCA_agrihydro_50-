# Flutter Application Architecture
## Smart Crop Water Requirement Prediction System

---

## Flutter Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    FLUTTER APPLICATION                        │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              PRESENTATION LAYER                        │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐│  │
│  │  │    Pages     │  │   Widgets    │  │  Providers   ││  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘│  │
│  └──────────────────────────────────────────────────────┘  │
│                           │                                  │
│                           ↓                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              DOMAIN LAYER                              │  │
│  │  ┌──────────────┐  ┌──────────────┐                  │  │
│  │  │   Entities   │  │   Use Cases  │                  │  │
│  │  └──────────────┘  └──────────────┘                  │  │
│  └──────────────────────────────────────────────────────┘  │
│                           │                                  │
│                           ↓                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              DATA LAYER                                │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐│  │
│  │  │   Models     │  │ Repositories │  │   Services   ││  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘│  │
│  └──────────────────────────────────────────────────────┘  │
│                           │                                  │
│                           ↓                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              CORE LAYER                                │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐│  │
│  │  │  Constants   │  │    Utils     │  │ Exceptions   ││  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘│  │
│  └──────────────────────────────────────────────────────┘  │
│                           │                                  │
│                           ↓                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              CONFIG LAYER                              │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐│  │
│  │  │ API Config   │  │  App Config  │  │ Theme Config ││  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘│  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                    FASTAPI BACKEND (REST API)                │
└─────────────────────────────────────────────────────────────┘
```

---

## App Architecture Pattern

### Clean Architecture (Modified for Flutter)

The app follows a modified Clean Architecture pattern suitable for Flutter:

1. **Presentation Layer**: UI components, state management, user interactions
2. **Domain Layer**: Business logic, use cases, entities
3. **Data Layer**: Data models, repositories, API services
4. **Core Layer**: Shared utilities, constants, exceptions
5. **Config Layer**: Configuration files

---

## Navigation Architecture

### Navigation Structure

```
SplashScreen
    │
    ↓
    ├─→ [Not Authenticated] → LoginScreen
    │                              │
    │                              ↓
    │                         RegisterScreen
    │                              │
    │                              ↓
    │                         [Authenticated]
    │
    └─→ [Authenticated] → MainScreen (Bottom Navigation)
                                  │
                                  ├─→ HomeTab → HomeDashboard
                                  │
                                  ├─→ FarmsTab → FarmListScreen
                                  │                     │
                                  │                     ├─→ AddFarmScreen
                                  │                     ├─→ FarmDetailScreen
                                  │                     └─→ FieldDetailScreen
                                  │
                                  ├─→ PredictionTab → CropSelectionScreen
                                  │                           │
                                  │                           ├─→ SoilInfoScreen
                                  │                           ├─→ GrowthStageScreen
                                  │                           ├─→ CWRPredictionScreen
                                  │                           └─→ PredictionResultScreen
                                  │
                                  ├─→ WeatherTab → WeatherDashboard
                                  │                           │
                                  │                           ├─→ CurrentWeatherScreen
                                  │                           └─→ WeatherForecastScreen
                                  │
                                  ├─→ AnalyticsTab → AnalyticsScreen
                                  │                           │
                                  │                           ├─→ HistoryScreen
                                  │                           ├─→ WaterUseTrackingScreen
                                  │                           └─→ DataQualityScreen
                                  │
                                  └─→ ProfileTab → ProfileScreen
                                                              │
                                                              ├─→ SettingsScreen
                                                              └─→ AdminDashboardScreen (Admin only)
```

### Route Definitions

```dart
// lib/routes/app_routes.dart
class AppRoutes {
  static const String splash = '/';
  static const String login = '/login';
  static const String register = '/register';
  static const String home = '/home';
  static const String farmList = '/farms';
  static const String addFarm = '/farms/add';
  static const String farmDetail = '/farms/:id';
  static const String fieldDetail = '/fields/:id';
  static const String cropSelection = '/crops/select';
  static const String soilInfo = '/soil/info';
  static const String growthStage = '/growth-stage';
  static const String cwrPrediction = '/prediction/cwr';
  static const String predictionResult = '/prediction/result/:id';
  static const String weatherDashboard = '/weather';
  static const String analytics = '/analytics';
  static const String history = '/history';
  static const String waterUseTracking = '/water-use';
  static const String dataQuality = '/data-quality';
  static const String profile = '/profile';
  static const String settings = '/settings';
  static const String adminDashboard = '/admin';
}
```

---

## Page Architecture

### 1. Splash Screen

**Purpose**: App initialization, authentication check

**Features**:
- App logo animation
- Loading indicator
- Authentication token check
- Auto-navigation to login or home

**Components**:
- `SplashPage` widget
- `SplashViewModel` (state management)
- `AuthCheckUseCase` (domain)

**Navigation Logic**:
```dart
if (hasValidToken) {
  navigateTo(HomeScreen);
} else {
  navigateTo(LoginScreen);
}
```

---

### 2. Login Screen

**Purpose**: Farmer authentication

**Input Fields**:
- Email (required)
- Password (required)

**Features**:
- Form validation
- Remember me option
- Forgot password link
- Social login (optional)
- Error handling

**Components**:
- `LoginPage` widget
- `LoginForm` widget
- `LoginProvider` (state management)
- `AuthRepository` (data)

**API Integration**:
- POST `/api/v1/auth/login`
- Store JWT token securely
- Navigate to home on success

---

### 3. Register Screen

**Purpose**: New farmer registration

**Input Fields**:
- Email (required)
- Password (required)
- Confirm Password (required)
- Full Name (required)
- Phone (required)
- State (dropdown)
- District (dropdown - state-dependent)
- Taluk (optional)

**Features**:
- Real-time validation
- Password strength indicator
- State/District cascading dropdowns
- Terms and conditions checkbox
- OTP verification (optional)

**Components**:
- `RegisterPage` widget
- `RegisterForm` widget
- `RegisterProvider` (state management)
- `AuthRepository` (data)

**API Integration**:
- POST `/api/v1/auth/register`
- Auto-login on success

---

### 4. Home Dashboard

**Purpose**: Main farmer dashboard with overview

**Layout**:
```
┌─────────────────────────────────────┐
│  Good Morning, [Farmer Name]        │
│  ┌───────────────────────────────┐  │
│  │  Current Farm: [Farm Name]    │  │
│  │  Crop: [Crop Name] 🌱         │  │
│  │  Growth Stage: [Stage]        │  │
│  └───────────────────────────────┘  │
│                                     │
│  ┌───────────────────────────────┐  │
│  │  CWR: 5.8 mm/day              │  │
│  │  Irrigation: 28.1 mm/week     │  │
│  │  Rainfall: 12.5 mm            │  │
│  │  Temperature: 29°C            │  │
│  └───────────────────────────────┘  │
│                                     │
│  [View Prediction] [Irrigation]     │
│                                     │
│  CWR Trend Chart                    │
│  ┌───────────────────────────────┐  │
│  │  [Interactive Chart]          │  │
│  └───────────────────────────────┘  │
│                                     │
│  Advisory                           │
│  ⚠ [Advisory Message]              │
│                                     │
│  Data Quality: ✓ Normal             │
└─────────────────────────────────────┘
```

**Features**:
- Current farm/crop display
- Key metrics cards
- CWR trend chart
- Quick action buttons
- Advisory alerts
- Data quality status

**Components**:
- `HomePage` widget
- `DashboardCard` widget
- `MetricCard` widget
- `CWRChart` widget
- `AdvisoryCard` widget
- `HomeProvider` (state management)

**API Integration**:
- GET `/api/v1/farms`
- GET `/api/v1/predictions/history?limit=1`
- GET `/api/v1/weather/current`
- GET `/api/v1/advisory`

---

### 5. Farm List Screen

**Purpose**: List all farms for the farmer

**Layout**:
```
┌─────────────────────────────────────┐
│  My Farms                    [+ Add]│
│                                     │
│  ┌───────────────────────────────┐  │
│  │  Farm 1: Main Field          │  │
│  │  Location: Bangalore Rural   │  │
│  │  Area: 5 acres               │  │
│  │  Status: Active              │  │
│  └───────────────────────────────┘  │
│                                     │
│  ┌───────────────────────────────┐  │
│  │  Farm 2: Secondary Field    │  │
│  │  Location: Bangalore Rural   │  │
│  │  Area: 3 acres               │  │
│  │  Status: Active              │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
```

**Features**:
- List of farms with cards
- Search/filter by name/location
- Add new farm button
- Tap to view farm details
- Swipe to delete (with confirmation)

**Components**:
- `FarmListPage` widget
- `FarmCard` widget
- `FarmListProvider` (state management)

**API Integration**:
- GET `/api/v1/farms`
- DELETE `/api/v1/farms/{id}`

---

### 6. Add Farm Screen

**Purpose**: Add a new farm

**Input Fields**:
- Farm Name (required)
- State (dropdown)
- District (dropdown - state-dependent)
- Taluk (optional)
- Latitude (auto-fill from map or manual)
- Longitude (auto-fill from map or manual)
- Total Area (required)
- Area Unit (dropdown: acres, hectares)

**Features**:
- Form validation
- Map integration for location
- State/District cascading dropdowns
- Area calculator (optional)

**Components**:
- `AddFarmPage` widget
- `FarmForm` widget
- `LocationPicker` widget
- `AddFarmProvider` (state management)

**API Integration**:
- POST `/api/v1/farms`

---

### 7. Farm Detail Screen

**Purpose**: View farm details and manage fields

**Layout**:
```
┌─────────────────────────────────────┐
│  Farm: Main Field          [Edit]   │
│  Location: Bangalore Rural         │
│  Area: 5 acres                     │
│                                     │
│  Fields                             │
│  ┌───────────────────────────────┐  │
│  │  Field 1: Paddy Field        │  │
│  │  Area: 2 acres               │  │
│  │  Crop: Paddy                 │  │
│  │  [View Details]             │  │
│  └───────────────────────────────┘  │
│                                     │
│  [+ Add Field]                      │
└─────────────────────────────────────┘
```

**Features**:
- Farm information display
- List of fields
- Add new field
- Edit farm details
- Delete farm

**Components**:
- `FarmDetailPage` widget
- `FieldCard` widget
- `FarmDetailProvider` (state management)

**API Integration**:
- GET `/api/v1/farms/{id}`
- PUT `/api/v1/farms/{id}`
- DELETE `/api/v1/farms/{id}`

---

### 8. Field Detail Screen

**Purpose**: View field details and manage crops

**Layout**:
```
┌─────────────────────────────────────┐
│  Field: Paddy Field         [Edit]  │
│  Area: 2 acres                      │
│  Soil Type: Clay Loam               │
│  Irrigation: Drip (85%)             │
│                                     │
│  Current Crop                        │
│  ┌───────────────────────────────┐  │
│  │  Paddy (IR64)                 │  │
│  │  Sowing: 2024-06-15           │  │
│  │  Stage: Development           │  │
│  │  [View Predictions]           │  │
│  └───────────────────────────────┘  │
│                                     │
│  [+ Plant New Crop]                 │
│                                     │
│  Soil Data                          │
│  ┌───────────────────────────────┐  │
│  │  pH: 6.5                      │  │
│  │  Nitrogen: 280 kg/ha          │  │
│  │  [Update Soil Data]           │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
```

**Features**:
- Field information display
- Current crop details
- Soil data display
- Plant new crop
- Update soil data
- View predictions

**Components**:
- `FieldDetailPage` widget
- `CropCard` widget
- `SoilDataCard` widget
- `FieldDetailProvider` (state management)

**API Integration**:
- GET `/api/v1/fields/{id}`
- GET `/api/v1/fields/{id}/soil-data`
- POST `/api/v1/fields/{id}/crops`

---

### 9. Crop Selection Screen

**Purpose**: Select crop for prediction

**Layout**:
```
┌─────────────────────────────────────┐
│  Select Crop                        │
│                                     │
│  Search: [________________] 🔍     │
│  Filter: [State] [Season]           │
│                                     │
│  ┌───────────────────────────────┐  │
│  │  🌾 Paddy                      │  │
│  │  Season: Kharif                │  │
│  │  Duration: 120 days            │  │
│  │  [Select]                      │  │
│  └───────────────────────────────┘  │
│                                     │
│  ┌───────────────────────────────┐  │
│  │  🌾 Ragi                       │  │
│  │  Season: Kharif                │  │
│  │  Duration: 105 days            │  │
│  │  [Select]                      │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
```

**Features**:
- Search crops by name
- Filter by state/season
- Crop cards with details
- Tap to select
- View crop details

**Components**:
- `CropSelectionPage` widget
- `CropCard` widget
- `SearchBar` widget
- `FilterChips` widget
- `CropProvider` (state management)

**API Integration**:
- GET `/api/v1/crops`
- GET `/api/v1/crops/{id}`

---

### 10. Soil Info Screen

**Purpose**: Enter or view soil information

**Input Fields**:
- pH Level (0-14)
- Nitrogen (kg/ha)
- Phosphorus (kg/ha)
- Potassium (kg/ha)
- Soil Moisture (%)
- Electrical Conductivity (dS/m)
- Organic Matter (%)
- Soil Texture (dropdown)

**Features**:
- Form validation
- Auto-fill from district soil data
- Manual entry option
- Soil health indicator

**Components**:
- `SoilInfoPage` widget
- `SoilForm` widget
- `SoilHealthIndicator` widget
- `SoilProvider` (state management)

**API Integration**:
- GET `/api/v1/soil/district/{state}/{district}`
- POST `/api/v1/fields/{field_id}/soil-data`

---

### 11. Growth Stage Screen

**Purpose**: Select or view crop growth stage

**Layout**:
```
┌─────────────────────────────────────┐
│  Crop: Paddy                        │
│  Sowing Date: 2024-06-15            │
│  Days After Sowing: 35             │
│                                     │
│  Current Growth Stage               │
│  ┌───────────────────────────────┐  │
│  │  Development/Tillering         │  │
│  │  Day 20-50                     │  │
│  │  Kc: 1.20                      │  │
│  │  ✓ Current Stage               │  │
│  └───────────────────────────────┘  │
│                                     │
│  All Stages                         │
│  ┌───────────────────────────────┐  │
│  │  1. Initial (Day 0-20)        │  │
│  │     Kc: 1.05                  │  │
│  │     ✓ Completed               │  │
│  └───────────────────────────────┘  │
│  ┌───────────────────────────────┐  │
│  │  2. Development (Day 20-50)   │  │
│  │     Kc: 1.20                  │  │
│  │     ● Current                 │  │
│  └───────────────────────────────┘  │
│  ┌───────────────────────────────┐  │
│  │  3. Mid-season (Day 50-80)   │  │
│  │     Kc: 1.35                  │  │
│  │     ○ Upcoming               │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
```

**Features**:
- Auto-calculate current stage based on sowing date
- Manual stage selection option
- Stage timeline visualization
- Kc value display

**Components**:
- `GrowthStagePage` widget
- `StageTimeline` widget
- `StageCard` widget
- `GrowthStageProvider` (state management)

**API Integration**:
- GET `/api/v1/crops/{crop_id}/growth-stages`
- PUT `/api/v1/field-crops/{id}`

---

### 12. CWR Prediction Screen

**Purpose**: Initiate CWR prediction

**Layout**:
```
┌─────────────────────────────────────┐
│  CWR Prediction                     │
│                                     │
│  Summary                            │
│  ┌───────────────────────────────┐  │
│  │  Crop: Paddy                   │  │
│  │  Field: Main Field             │  │
│  │  Growth Stage: Development     │  │
│  │  Area: 2 acres                 │  │
│  └───────────────────────────────┘  │
│                                     │
│  Weather Data                       │
│  ┌───────────────────────────────┐  │
│  │  Temperature: 29°C            │  │
│  │  Humidity: 65%                │  │
│  │  Rainfall: 0 mm               │  │
│  │  [Refresh]                    │  │
│  └───────────────────────────────┘  │
│                                     │
│  Soil Data                          │
│  ┌───────────────────────────────┐  │
│  │  pH: 6.5                      │  │
│  │  Nitrogen: 280 kg/ha          │  │
│  │  [Edit]                       │  │
│  └───────────────────────────────┘  │
│                                     │
│  [Predict CWR]                      │
└─────────────────────────────────────┘
```

**Features**:
- Display prediction inputs
- Refresh weather data
- Edit soil data
- Initiate prediction
- Loading state during prediction

**Components**:
- `CWRPredictionPage` widget
- `PredictionSummaryCard` widget
- `WeatherDataCard` widget
- `SoilDataCard` widget
- `PredictionProvider` (state management)

**API Integration**:
- GET `/api/v1/weather/current`
- POST `/api/v1/predictions/cwr`

---

### 13. Prediction Result Screen

**Purpose**: Display CWR prediction results

**Layout**:
```
┌─────────────────────────────────────┐
│  CROP WATER REQUIREMENT             │
│                                     │
│  🌱 Paddy                           │
│  📍 Karnataka                       │
│  Growth Stage: Development          │
│  Farm Area: 2 acres                 │
│                                     │
│  ┌───────────────────────────────┐  │
│  │  Predicted CWR                │  │
│  │  5.8 mm/day                   │  │
│  └───────────────────────────────┘  │
│                                     │
│  ┌───────────────────────────────┐  │
│  │  Weekly Requirement            │  │
│  │  40.6 mm/week                 │  │
│  └───────────────────────────────┘  │
│                                     │
│  ┌───────────────────────────────┐  │
│  │  Effective Rainfall            │  │
│  │  12.5 mm/week                 │  │
│  └───────────────────────────────┘  │
│                                     │
│  ┌───────────────────────────────┐  │
│  │  Irrigation Requirement        │  │
│  │  28.1 mm/week                 │  │
│  └───────────────────────────────┘  │
│                                     │
│  WHY THIS PREDICTION?               │
│  Temperature       ████████ 35%     │
│  Growth Stage      █████████ 28%    │
│  Rainfall          ███ 20%          │
│  Humidity          █████ 12%        │
│  Soil              ██████ 5%        │
│                                     │
│  WEATHER FORECAST                   │
│  [Next 5-7 days forecast]           │
│                                     │
│  FARMER ADVISORY                    │
│  ⚠ [Advisory message]              │
│                                     │
│  [View Historical] [Record Water]   │
└─────────────────────────────────────┘
```

**Features**:
- CWR metrics display
- Feature importance visualization
- Weather forecast
- Farmer advisory
- Action buttons

**Components**:
- `PredictionResultPage` widget
- `CWRMetricCard` widget
- `FeatureImportanceChart` widget
- `WeatherForecastCard` widget
- `AdvisoryCard` widget
- `PredictionResultProvider` (state management)

**API Integration**:
- GET `/api/v1/predictions/{id}`
- GET `/api/v1/predictions/{id}/explanation`
- GET `/api/v1/weather/forecast`
- GET `/api/v1/advisory`

---

### 14. Weather Dashboard

**Purpose**: Display weather information

**Layout**:
```
┌─────────────────────────────────────┐
│  Weather Dashboard                   │
│  Location: Bangalore Rural          │
│                                     │
│  Current Weather                    │
│  ┌───────────────────────────────┐  │
│  │  ☀️ 29°C                      │  │
│  │  Humidity: 65%                │  │
│  │  Wind: 12 km/h                │  │
│  │  Rainfall: 0 mm               │  │
│  └───────────────────────────────┘  │
│                                     │
│  7-Day Forecast                     │
│  ┌───────────────────────────────┐  │
│  │  Mon  Tue  Wed  Thu  Fri      │  │
│  │  29°  30°  28°  27°  29°      │  │
│  │  🌧️   ☀️   ☀️   ☀️   ☀️      │  │
│  └───────────────────────────────┘  │
│                                     │
│  Historical Weather                 │
│  [Historical weather chart]          │
└─────────────────────────────────────┘
```

**Features**:
- Current weather display
- Weather forecast
- Historical weather chart
- Location selection

**Components**:
- `WeatherDashboardPage` widget
- `CurrentWeatherCard` widget
- `ForecastCard` widget
- `WeatherChart` widget
- `WeatherProvider` (state management)

**API Integration**:
- GET `/api/v1/weather/current`
- GET `/api/v1/weather/forecast`
- GET `/api/v1/weather/historical`

---

### 15. Analytics Screen

**Purpose**: Display analytics and charts

**Layout**:
```
┌─────────────────────────────────────┐
│  Analytics                          │
│                                     │
│  Time Range: [Last 30 Days ▼]       │
│                                     │
│  CWR Trend                          │
│  ┌───────────────────────────────┐  │
│  │  [CWR over time chart]         │  │
│  └───────────────────────────────┘  │
│                                     │
│  Rainfall vs CWR                    │
│  ┌───────────────────────────────┐  │
│  │  [Rainfall vs CWR chart]       │  │
│  └───────────────────────────────┘  │
│                                     │
│  Growth Stage Water Requirement      │
│  ┌───────────────────────────────┐  │
│  │  [Stage-wise CWR chart]       │  │
│  └───────────────────────────────┘  │
│                                     │
│  Predicted vs Actual Water Use      │
│  ┌───────────────────────────────┐  │
│  │  [Prediction vs Actual chart]  │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
```

**Features**:
- Multiple chart types
- Time range filter
- Interactive charts
- Export data (optional)

**Components**:
- `AnalyticsPage` widget
- `CWRChart` widget
- `RainfallCWRChart` widget
- `GrowthStageChart` widget
- `PredictionActualChart` widget
- `AnalyticsProvider` (state management)

**API Integration**:
- GET `/api/v1/analytics/cwr`
- GET `/api/v1/analytics/rainfall-cwr`
- GET `/api/v1/analytics/water-use`

---

### 16. History Screen

**Purpose**: View prediction history

**Layout**:
```
┌─────────────────────────────────────┐
│  Prediction History                 │
│  Filter: [Crop] [Date Range]        │
│                                     │
│  ┌───────────────────────────────┐  │
│  │  2024-06-20                    │  │
│  │  Crop: Paddy                  │  │
│  │  CWR: 5.8 mm/day              │  │
│  │  Irrigation: 28.1 mm/week     │  │
│  │  [View Details]               │  │
│  └───────────────────────────────┘  │
│                                     │
│  ┌───────────────────────────────┐  │
│  │  2024-06-15                    │  │
│  │  Crop: Paddy                  │  │
│  │  CWR: 5.2 mm/day              │  │
│  │  Irrigation: 25.0 mm/week     │  │
│  │  [View Details]               │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
```

**Features**:
- List of past predictions
- Filter by crop/date
- View prediction details
- Export history (optional)

**Components**:
- `HistoryPage` widget
- `PredictionHistoryCard` widget
- `HistoryProvider` (state management)

**API Integration**:
- GET `/api/v1/predictions/history`

---

### 17. Water Use Tracking Screen

**Purpose**: Record and view water use

**Layout**:
```
┌─────────────────────────────────────┐
│  Water Use Tracking                 │
│                                     │
│  Record Water Use                   │
│  ┌───────────────────────────────┐  │
│  │  Date: [2024-06-20]           │  │
│  │  Water Used: [30] mm          │  │
│  │  Source: [Borewell ▼]         │  │
│  │  Area: [2] acres              │  │
│  │  Cost: [150] ₹                │  │
│  │  [Save]                       │  │
│  └───────────────────────────────┘  │
│                                     │
│  Water Use History                  │
│  ┌───────────────────────────────┐  │
│  │  2024-06-20: 30 mm            │  │
│  │  2024-06-17: 28 mm            │  │
│  │  2024-06-14: 32 mm            │  │
│  └───────────────────────────────┘  │
│                                     │
│  Predicted vs Actual                 │
│  [Comparison chart]                 │
└─────────────────────────────────────┘
```

**Features**:
- Record water use
- View water use history
- Predicted vs actual comparison
- Cost tracking

**Components**:
- `WaterUseTrackingPage` widget
- `WaterUseForm` widget
- `WaterUseHistoryCard` widget
- `WaterUseProvider` (state management)

**API Integration**:
- POST `/api/v1/water-use`
- GET `/api/v1/water-use`
- GET `/api/v1/analytics/water-use`

---

### 18. Data Quality Screen

**Purpose**: Display data quality alerts

**Layout**:
```
┌─────────────────────────────────────┐
│  Data Quality                       │
│  Overall Status: ✓ Normal          │
│                                     │
│  Recent Alerts                      │
│  ┌───────────────────────────────┐  │
│  │  ⚠ Warning                   │  │
│  │  Rainfall value unusually high│  │
│  │  Detected: 85 mm             │  │
│  │  Expected: 0-30 mm           │  │
│  │  Date: 2024-06-20            │  │
│  └───────────────────────────────┘  │
│                                     │
│  Data Quality Summary               │
│  ┌───────────────────────────────┐  │
│  │  Weather Data: ✓ Valid        │  │
│  │  Completeness: 100%           │  │
│  └───────────────────────────────┘  │
│  ┌───────────────────────────────┐  │
│  │  Soil Data: ✓ Valid          │  │
│  │  Completeness: 85%            │  │
│  └───────────────────────────────┘  │
│  ┌───────────────────────────────┐  │
│  │  Rainfall Data: ⚠ Warning    │  │
│  │  Completeness: 100%           │  │
│  │  Anomaly Detected             │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
```

**Features**:
- Data quality status
- Anomaly alerts
- Data completeness
- Data validation summary

**Components**:
- `DataQualityPage` widget
- `AlertCard` widget
- `QualitySummaryCard` widget
- `DataQualityProvider` (state management)

**API Integration**:
- GET `/api/v1/data-quality/anomalies`
- GET `/api/v1/data-quality/summary`

---

### 19. Profile Screen

**Purpose**: User profile and settings

**Layout**:
```
┌─────────────────────────────────────┐
│  Profile                            │
│                                     │
│  ┌───────────────────────────────┐  │
│  │  [Avatar]                      │  │
│  │  Ramesh Kumar                  │  │
│  │  farmer@example.com           │  │
│  │  +919876543210                 │  │
│  │  [Edit Profile]               │  │
│  └───────────────────────────────┘  │
│                                     │
│  Settings                           │
│  [Notifications]                    │
│  [Language]                        │
│  [Units]                           │
│  [Theme]                           │
│                                     │
│  Account                            │
│  [Change Password]                 │
│  [Privacy Policy]                  │
│  [Terms of Service]                │
│  [Logout]                          │
└─────────────────────────────────────┘
```

**Features**:
- Profile display
- Edit profile
- App settings
- Account management
- Logout

**Components**:
- `ProfilePage` widget
- `ProfileCard` widget
- `SettingsList` widget
- `ProfileProvider` (state management)

**API Integration**:
- GET `/api/v1/farmers/profile`
- PUT `/api/v1/farmers/profile`
- POST `/api/v1/auth/logout`

---

### 20. Settings Screen

**Purpose**: App settings

**Settings Options**:
- Notifications (toggle)
- Language (dropdown)
- Units (metric/imperial)
- Theme (light/dark/auto)
- Data sync (toggle)
- Cache clear

**Components**:
- `SettingsPage` widget
- `SettingItem` widget
- `SettingsProvider` (state management)

---

### 21. Admin Dashboard (Admin Only)

**Purpose**: Research/admin dashboard

**Layout**:
```
┌─────────────────────────────────────┐
│  Admin Dashboard                    │
│                                     │
│  Model Performance                  │
│  ┌───────────────────────────────┐  │
│  │  Random Forest                │  │
│  │  MAE: 0.42                    │  │
│  │  RMSE: 0.62                   │  │
│  │  R²: 0.89                     │  │
│  └───────────────────────────────┘  │
│  ┌───────────────────────────────┐  │
│  │  Gradient Boosting            │  │
│  │  MAE: 0.38                    │  │
│  │  RMSE: 0.55                   │  │
│  │  R²: 0.91                     │  │
│  │  ✓ Best Model                 │  │
│  └───────────────────────────────┘  │
│                                     │
│  Dataset Statistics                 │
│  ┌───────────────────────────────┐  │
│  │  Crop Data: 150 records       │  │
│  │  Soil Data: 500 records       │  │
│  │  Weather Data: 10,000 records │  │
│  │  Overall Quality: 98.5%       │  │
│  └───────────────────────────────┘  │
│                                     │
│  Prediction Statistics              │
│  ┌───────────────────────────────┐  │
│  │  Total Predictions: 1,250     │  │
│  │  Average Confidence: 82%      │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
```

**Features**:
- Model performance display
- Dataset statistics
- Prediction statistics
- Feature importance charts
- Model comparison charts

**Components**:
- `AdminDashboardPage` widget
- `ModelPerformanceCard` widget
- `DatasetStatsCard` widget
- `AdminProvider` (state management)

**API Integration**:
- GET `/api/v1/admin/model-performance`
- GET `/api/v1/admin/dataset-statistics`
- GET `/api/v1/admin/prediction-statistics`

---

## State Management Architecture

### Provider Pattern

The app uses the Provider package for state management:

```dart
// lib/presentation/providers/auth_provider.dart
class AuthProvider with ChangeNotifier {
  AuthModel? _user;
  bool _isLoading = false;
  String? _errorMessage;

  AuthModel? get user => _user;
  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;
  bool get isAuthenticated => _user != null;

  Future<void> login(String email, String password) async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      final authRepository = AuthRepository();
      final result = await authRepository.login(email, password);
      _user = result;
      await _saveToken(result.token);
    } catch (e) {
      _errorMessage = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> logout() async {
    _user = null;
    await _clearToken();
    notifyListeners();
  }
}
```

### Provider Hierarchy

```
MultiProvider
├── AuthProvider
├── FarmProvider
├── CropProvider
├── WeatherProvider
├── PredictionProvider
├── AnalyticsProvider
└── AdminProvider
```

---

## Widget Architecture

### Common Widgets

```dart
// lib/presentation/widgets/common/custom_button.dart
class CustomButton extends StatelessWidget {
  final String text;
  final VoidCallback onPressed;
  final bool isLoading;
  final Color? backgroundColor;

  const CustomButton({
    required this.text,
    required this.onPressed,
    this.isLoading = false,
    this.backgroundColor,
  });

  @override
  Widget build(BuildContext context) {
    return ElevatedButton(
      onPressed: isLoading ? null : onPressed,
      style: ElevatedButton.styleFrom(
        backgroundColor: backgroundColor ?? Theme.of(context).primaryColor,
        padding: EdgeInsets.symmetric(horizontal: 24, vertical: 16),
      ),
      child: isLoading
          ? CircularProgressIndicator(color: Colors.white)
          : Text(text),
    );
  }
}
```

### Chart Widgets

```dart
// lib/presentation/widgets/charts/cwr_trend_chart.dart
class CWRTrendChart extends StatelessWidget {
  final List<CWRDataPoint> data;

  const CWRTrendChart({required this.data});

  @override
  Widget build(BuildContext context) {
    return LineChart(
      LineChartData(
        lineBarsData: [
          LineChartBarData(
            spots: data.map((point) => FlSpot(point.date.day.toDouble(), point.cwr)).toList(),
            isCurved: true,
            color: Theme.of(context).primaryColor,
            barWidth: 3,
          ),
        ],
      ),
    );
  }
}
```

---

## Theme Architecture

### App Theme

```dart
// lib/core/theme/app_theme.dart
class AppTheme {
  static ThemeData get lightTheme {
    return ThemeData(
      primaryColor: AppColors.primary,
      scaffoldBackgroundColor: AppColors.background,
      textTheme: AppTextStyles.textTheme,
      cardTheme: CardTheme(
        elevation: 2,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      ),
    );
  }

  static ThemeData get darkTheme {
    return ThemeData(
      primaryColor: AppColors.primaryDark,
      scaffoldBackgroundColor: AppColors.backgroundDark,
      textTheme: AppTextStyles.textThemeDark,
      cardTheme: CardTheme(
        elevation: 2,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      ),
    );
  }
}
```

### Color Palette

```dart
// lib/core/theme/app_colors.dart
class AppColors {
  static const Color primary = Color(0xFF2E7D32); // Green
  static const Color primaryDark = Color(0xFF1B5E20);
  static const Color secondary = Color(0xFF1976D2); // Blue
  static const Color accent = Color(0xFFFF9800); // Orange
  static const Color background = Color(0xFFF5F5F5);
  static const Color backgroundDark = Color(0xFF121212);
  static const Color card = Color(0xFFFFFFFF);
  static const Color cardDark = Color(0xFF1E1E1E);
  static const Color text = Color(0xFF212121);
  static const Color textDark = Color(0xFFFFFFFF);
  static const Color error = Color(0xFFD32F2F);
  static const Color success = Color(0xFF388E3C);
  static const Color warning = Color(0xFFFFA000);
}
```

---

## API Service Architecture

### API Client

```dart
// lib/data/services/api_service.dart
class APIService {
  final Dio _dio;

  APIService() : _dio = Dio(BaseOptions(
    baseUrl: ApiConfig.baseUrl,
    connectTimeout: Duration(seconds: 30),
    receiveTimeout: Duration(seconds: 30),
  )) {
    _dio.interceptors.add(AuthInterceptor());
    _dio.interceptors.add(LogInterceptor());
  }

  Future<Response> get(String path, {Map<String, dynamic>? queryParameters}) {
    return _dio.get(path, queryParameters: queryParameters);
  }

  Future<Response> post(String path, {dynamic data}) {
    return _dio.post(path, data: data);
  }

  Future<Response> put(String path, {dynamic data}) {
    return _dio.put(path, data: data);
  }

  Future<Response> delete(String path) {
    return _dio.delete(path);
  }
}
```

### Auth Interceptor

```dart
// lib/data/services/auth_interceptor.dart
class AuthInterceptor extends Interceptor {
  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) async {
    final token = await StorageService.getToken();
    if (token != null) {
      options.headers['Authorization'] = 'Bearer $token';
    }
    handler.next(options);
  }

  @override
  void onError(DioError err, ErrorInterceptorHandler handler) async {
    if (err.response?.statusCode == 401) {
      // Token expired, refresh or logout
      await StorageService.clearToken();
      // Navigate to login
    }
    handler.next(err);
  }
}
```

---

## Error Handling Architecture

### Error Types

```dart
// lib/core/exceptions/app_exceptions.dart
class AppException implements Exception {
  final String message;
  final String? code;

  AppException(this.message, [this.code]);

  @override
  String toString() => message;
}

class NetworkException extends AppException {
  NetworkException(String message) : super(message, 'NETWORK_ERROR');
}

class AuthException extends AppException {
  AuthException(String message) : super(message, 'AUTH_ERROR');
}

class ValidationException extends AppException {
  ValidationException(String message) : super(message, 'VALIDATION_ERROR');
}

class ServerException extends AppException {
  ServerException(String message) : super(message, 'SERVER_ERROR');
}
```

### Error Display

```dart
// lib/presentation/widgets/common/error_widget.dart
class ErrorWidget extends StatelessWidget {
  final String message;
  final VoidCallback? onRetry;

  const ErrorWidget({required this.message, this.onRetry});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.error_outline, size: 64, color: AppColors.error),
          SizedBox(height: 16),
          Text(message, style: TextStyle(color: AppColors.error)),
          if (onRetry != null) ...[
            SizedBox(height: 16),
            ElevatedButton(onPressed: onRetry, child: Text('Retry')),
          ],
        ],
      ),
    );
  }
}
```

---

## Form Validation Architecture

### Validators

```dart
// lib/core/utils/validators.dart
class Validators {
  static String? validateEmail(String? value) {
    if (value == null || value.isEmpty) {
      return 'Email is required';
    }
    final emailRegex = RegExp(r'^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$');
    if (!emailRegex.hasMatch(value)) {
      return 'Enter a valid email';
    }
    return null;
  }

  static String? validatePassword(String? value) {
    if (value == null || value.isEmpty) {
      return 'Password is required';
    }
    if (value.length < 6) {
      return 'Password must be at least 6 characters';
    }
    return null;
  }

  static String? validateRequired(String? value, String fieldName) {
    if (value == null || value.isEmpty) {
      return '$fieldName is required';
    }
    return null;
  }

  static String? validateNumber(String? value, String fieldName) {
    if (value == null || value.isEmpty) {
      return '$fieldName is required';
    }
    final number = double.tryParse(value);
    if (number == null) {
      return 'Enter a valid number';
    }
    return null;
  }
}
```

---

## Loading States Architecture

### Loading Indicator

```dart
// lib/presentation/widgets/common/loading_indicator.dart
class LoadingIndicator extends StatelessWidget {
  final String? message;

  const LoadingIndicator({this.message});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          CircularProgressIndicator(),
          if (message != null) ...[
            SizedBox(height: 16),
            Text(message!),
          ],
        ],
      ),
    );
  }
}
```

---

## Responsive Design Architecture

### Responsive Layout

```dart
// lib/core/utils/responsive_utils.dart
class ResponsiveUtils {
  static bool isMobile(BuildContext context) {
    return MediaQuery.of(context).size.width < 600;
  }

  static bool isTablet(BuildContext context) {
    return MediaQuery.of(context).size.width >= 600 &&
           MediaQuery.of(context).size.width < 1200;
  }

  static bool isDesktop(BuildContext context) {
    return MediaQuery.of(context).size.width >= 1200;
  }

  static double getWidth(BuildContext context, double percentage) {
    return MediaQuery.of(context).size.width * percentage;
  }
}
```

---

## Key Design Decisions

### 1. Clean Architecture
- **Reason**: Separation of concerns, testability, scalability
- **Implementation**: Domain, Data, Presentation layers

### 2. Provider for State Management
- **Reason**: Simple, Flutter-recommended, good performance
- **Implementation**: ChangeNotifier with Consumer widgets

### 3. Bottom Navigation
- **Reason**: Easy navigation, farmer-friendly
- **Implementation**: 5 main tabs (Home, Farms, Prediction, Weather, Analytics)

### 4. Card-Based UI
- **Reason**: Modern, organized, easy to scan
- **Implementation**: Consistent card widgets throughout

### 5. Interactive Charts
- **Reason**: Data visualization, research support
- **Implementation**: FL Chart library for Flutter

### 6. Farmer-Friendly Terminology
- **Reason**: Accessibility for non-technical users
- **Implementation**: Simple language, clear labels

### 7. Offline Support (Future)
- **Reason**: Rural areas with poor connectivity
- **Implementation**: Local caching with Hive

### 8. Material Design 3
- **Reason**: Modern UI, consistent look
- **Implementation**: Material 3 components and theming
