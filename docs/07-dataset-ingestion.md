# Dataset Ingestion Architecture
## Smart Crop Water Requirement Prediction System

---

## Dataset Ingestion Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    DATASET SOURCES                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Crop    │  │  Soil    │  │ Weather  │  │ Rainfall │   │
│  │  Catalog │  │  Data    │  │  Data    │  │  Data    │   │
│  │  (CSV)   │  │  (CSV)   │  │  (CSV)   │  │  (CSV)   │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Growth   │  │ ET0      │  │ Irrig.   │  │ Market   │   │
│  │ Stage    │  │ Reference│  │ Efficiency│  │ Price    │   │
│  │  (CSV)   │  │  (CSV)   │  │  (CSV)   │  │  (CSV)   │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              DATASET INGESTION PIPELINE                      │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  1. Dataset Discovery                                 │   │
│  │     - Scan datasets directory                         │   │
│  │     - Identify new/updated files                     │   │
│  │     - Validate file formats                          │   │
│  └──────────────────────────────────────────────────────┘   │
│                           │                                  │
│                           ↓                                  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  2. Schema Validation                                 │   │
│  │     - Validate column names                           │   │
│  │     - Validate data types                             │   │
│  │     - Validate required columns                       │   │
│  │     - Validate value ranges                           │   │
│  └──────────────────────────────────────────────────────┘   │
│                           │                                  │
│                           ↓                                  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  3. Data Loading                                      │   │
│  │     - Load CSV/JSON/Excel files                      │   │
│  │     - Handle encoding issues                         │   │
│  │     - Parse dates                                    │   │
│  │     - Handle missing values                          │   │
│  └──────────────────────────────────────────────────────┘   │
│                           │                                  │
│                           ↓                                  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  4. Data Cleaning                                    │   │
│  │     - Remove duplicates                              │   │
│  │     - Fix inconsistencies                            │   │
│  │     - Standardize formats                            │   │
│  │     - Handle outliers                                │   │
│  └──────────────────────────────────────────────────────┘   │
│                           │                                  │
│                           ↓                                  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  5. Data Transformation                              │   │
│  │     - Map to database schema                         │   │
│  │     - Transform data types                           │   │
│  │     - Create foreign key relationships               │   │
│  │     - Generate derived fields                       │   │
│  └──────────────────────────────────────────────────────┘   │
│                           │                                  │
│                           ↓                                  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  6. Data Quality Checks                               │   │
│  │     - Completeness checks                            │   │
│  │     - Accuracy checks                                │   │
│  │     - Consistency checks                              │   │
│  │     - Generate quality report                        │   │
│  └──────────────────────────────────────────────────────┘   │
│                           │                                  │
│                           ↓                                  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  7. Database Insertion                               │   │
│  │     - Batch insert operations                        │   │
│  │     - Handle foreign key constraints                 │   │
│  │     - Transaction management                         │   │
│  │     - Error handling & rollback                      │   │
│  └──────────────────────────────────────────────────────┘   │
│                           │                                  │
│                           ↓                                  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  8. Metadata Storage                                 │   │
│  │     - Record ingestion timestamp                     │   │
│  │     - Store source file info                         │   │
│  │     - Record record counts                           │   │
│  │     - Store quality metrics                          │   │
│  └──────────────────────────────────────────────────────┘   │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    POSTGRESQL DATABASE                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  crops   │  │  soil    │  │ weather  │  │ rainfall │   │
│  │  table   │  │  table   │  │  table   │  │  table   │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## Dataset Categories

### 1. Crop Information Dataset

**Purpose**: Crop catalog and crop characteristics

**File**: `datasets/crop/crop_catalog.csv`

**Schema**:
```csv
crop_id,name,scientific_name,category,growing_season,duration_days,description
1,Paddy,Oryza sativa,Cereal,Kharif,120,Main staple crop
2,Ragi,Eleusine coracana,Cereal,Kharif,105,Millets
3,Maize,Zea mays,Cereal,Kharif,110,Cereal crop
4,Arecanut,Areca catechu,Plantation,Perennial,Perennial,Plantation crop
5,Sugarcane,Saccharum officinarum,Plantation,Perennial,365,Industrial crop
6,Cotton,Gossypium hirsutum,Fiber,Kharif,180,Fiber crop
7,Soybean,Glycine max,Legume,Kharif,90,Legume crop
8,Groundnut,Arachis hypogaea,Legume,Kharif,100,Oilseed crop
```

**Validation Rules**:
- `crop_id`: Unique integer
- `name`: Required, unique
- `scientific_name`: Optional
- `category`: Required (Cereal, Legume, Plantation, Fiber, Oilseed)
- `growing_season`: Required (Kharif, Rabi, Summer, Perennial)
- `duration_days`: Required, positive integer

---

### 2. Crop Varieties Dataset

**Purpose**: Crop variety information

**File**: `datasets/crop/crop_varieties.csv`

**Schema**:
```csv
variety_id,crop_id,name,description,characteristics,yield_potential,duration_days
1,1,IR64,High yield variety,High yield,5.5,120
2,1,Samba,Traditional variety,Medium yield,4.5,135
3,2,Indaf-5,Improved variety,High yield,2.5,105
4,5,Co-86032,High sugar variety,High sugar content,120,365
```

**Validation Rules**:
- `variety_id`: Unique integer
- `crop_id`: Foreign key to crops table
- `name`: Required
- `duration_days`: Positive integer

---

### 3. Crop Growth Stage Dataset

**Purpose**: Growth stage information with Kc values

**File**: `datasets/growth_stage/crop_growth_stages.csv`

**Schema**:
```csv
stage_id,crop_id,stage_name,stage_order,duration_days,kc_value,description,source
1,1,Initial/Establishment,1,20,1.05,Seedling establishment,FAO-56
2,1,Development/Tillering,2,30,1.20,Tillering and vegetative growth,FAO-56
3,1,Mid-season/Flowering,3,35,1.35,Flowering and grain filling,FAO-56
4,1,Late-season/Maturity,4,25,1.10,Grain maturation,FAO-56
5,1,Harvest,5,10,0.90,Harvesting phase,FAO-56
```

**Validation Rules**:
- `stage_id`: Unique integer
- `crop_id`: Foreign key to crops table
- `stage_name`: Required
- `stage_order`: Required, unique per crop
- `duration_days`: Positive integer
- `kc_value`: Required, positive decimal (0.5-1.5 typical range)
- `source`: Required (FAO-56, ICAR, Local Research)

---

### 4. Soil Dataset

**Purpose**: Soil parameters by district

**File**: `datasets/soil/soil_parameters.csv`

**Schema**:
```csv
soil_id,state,district,dominant_soil_type,ph_avg,nitrogen_avg,phosphorus_avg,potassium_avg,organic_matter_avg,texture,source
1,Karnataka,Bangalore Rural,Red Sandy Loam,6.5,280,45,210,1.2,Sandy Loam,ICAR
2,Karnataka,Mysore,Clay Loam,6.8,320,52,245,1.5,Clay Loam,ICAR
3,Maharashtra,Pune,Black Soil,7.2,350,48,230,1.4,Clay,ICAR
4,Tamil Nadu,Coimbatore,Red Soil,6.3,260,42,200,1.1,Sandy Clay Loam,ICAR
```

**Validation Rules**:
- `soil_id`: Unique integer
- `state`: Required
- `district`: Required
- `ph_avg`: Required, 0-14 range
- `nitrogen_avg`: Required, positive
- `phosphorus_avg`: Required, positive
- `potassium_avg`: Required, positive
- `organic_matter_avg`: Required, 0-10 range

---

### 5. Historical Weather Dataset

**Purpose**: Historical weather data for ML training

**File**: `datasets/weather/historical_weather.csv`

**Schema**:
```csv
weather_id,district,date,temperature_max,temperature_min,temperature_avg,humidity,wind_speed,rainfall,solar_radiation,et0,data_source
1,Bangalore Rural,2020-01-01,28.5,18.2,23.5,65,12,0,18.5,4.2,IMD
2,Bangalore Rural,2020-01-02,29.0,18.5,24.0,63,11,0,19.0,4.3,IMD
3,Bangalore Rural,2020-01-03,27.5,17.8,22.5,68,13,2.5,17.0,4.0,IMD
```

**Validation Rules**:
- `weather_id`: Unique integer
- `district`: Required
- `date`: Required, valid date format
- `temperature_max`: Required, -50 to 60°C range
- `temperature_min`: Required, -50 to 60°C range
- `temperature_avg`: Required, -50 to 60°C range
- `humidity`: Required, 0-100 range
- `wind_speed`: Required, 0-100 km/h range
- `rainfall`: Required, 0-500 mm range
- `solar_radiation`: Optional, 0-30 MJ/m²/day range
- `et0`: Optional, positive
- `data_source`: Required (IMD, NOAA, Local)

---

### 6. Historical Rainfall Dataset

**Purpose**: Historical rainfall data

**File**: `datasets/rainfall/historical_rainfall.csv`

**Schema**:
```csv
rainfall_id,district,date,daily_rainfall,weekly_rainfall,monthly_rainfall,seasonal_rainfall,data_source
1,Bangalore Rural,2020-01-01,0,0,0,0,IMD
2,Bangalore Rural,2020-06-15,25,150,450,1200,IMD
3,Bangalore Rural,2020-06-16,30,180,480,1230,IMD
```

**Validation Rules**:
- `rainfall_id`: Unique integer
- `district`: Required
- `date`: Required
- `daily_rainfall`: Required, 0-500 mm range
- `weekly_rainfall`: Optional, 0-1000 mm range
- `monthly_rainfall`: Optional, 0-2000 mm range
- `seasonal_rainfall`: Optional, 0-5000 mm range

---

### 7. ET0 Reference Dataset

**Purpose**: Reference evapotranspiration data

**File**: `datasets/reference/et0_reference.csv`

**Schema**:
```csv
et0_id,district,date,et0,method,latitude,longitude,altitude
1,Bangalore Rural,2020-01-01,4.2,Penman-Monteith,13.0,77.5,920
2,Bangalore Rural,2020-06-15,6.8,Penman-Monteith,13.0,77.5,920
```

**Validation Rules**:
- `et0_id`: Unique integer
- `district`: Required
- `date`: Required
- `et0`: Required, positive
- `method`: Required (Penman-Monteith, Hargreaves, Priestley-Taylor)
- `latitude`: Required, -90 to 90 range
- `longitude`: Required, -180 to 180 range
- `altitude`: Required, meters

---

### 8. Irrigation Efficiency Dataset

**Purpose**: Irrigation method efficiency values

**File**: `datasets/reference/irrigation_efficiency.csv`

**Schema**:
```csv
efficiency_id,irrigation_method,efficiency_range,typical_efficiency,description
1,Drip,0.85-0.95,0.90,High efficiency drip irrigation
2,Sprinkler,0.70-0.80,0.75,Moderate efficiency sprinkler
3,Flood,0.40-0.60,0.50,Low efficiency flood irrigation
4,Furrow,0.50-0.70,0.60,Moderate efficiency furrow irrigation
```

**Validation Rules**:
- `efficiency_id`: Unique integer
- `irrigation_method`: Required, unique
- `efficiency_range`: Required
- `typical_efficiency`: Required, 0-1 range
- `description`: Optional

---

## Ingestion Pipeline Implementation

### Dataset Ingestion Service

```python
# backend/scripts/dataset_ingestion.py
import pandas as pd
import logging
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatasetIngestionService:
    def __init__(self, db_url: str, datasets_dir: str = "datasets"):
        self.db_url = db_url
        self.datasets_dir = Path(datasets_dir)
        self.engine = create_engine(db_url)
        self.ingestion_log = []
    
    def ingest_all_datasets(self) -> Dict[str, any]:
        """Ingest all datasets from the datasets directory"""
        results = {
            'success': True,
            'datasets': {},
            'errors': []
        }
        
        # Define dataset configurations
        dataset_configs = [
            {
                'name': 'crop_catalog',
                'file': 'crop/crop_catalog.csv',
                'table': 'crops',
                'schema': self._get_crop_schema()
            },
            {
                'name': 'crop_varieties',
                'file': 'crop/crop_varieties.csv',
                'table': 'crop_varieties',
                'schema': self._get_variety_schema()
            },
            {
                'name': 'growth_stages',
                'file': 'growth_stage/crop_growth_stages.csv',
                'table': 'crop_growth_stages',
                'schema': self._get_growth_stage_schema()
            },
            {
                'name': 'soil_data',
                'file': 'soil/soil_parameters.csv',
                'table': 'district_soil_map',
                'schema': self._get_soil_schema()
            },
            {
                'name': 'weather_data',
                'file': 'weather/historical_weather.csv',
                'table': 'weather_data',
                'schema': self._get_weather_schema()
            },
            {
                'name': 'rainfall_data',
                'file': 'rainfall/historical_rainfall.csv',
                'table': 'rainfall_data',
                'schema': self._get_rainfall_schema()
            }
        ]
        
        for config in dataset_configs:
            try:
                result = self.ingest_dataset(config)
                results['datasets'][config['name']] = result
                logger.info(f"Successfully ingested {config['name']}")
            except Exception as e:
                error_msg = f"Failed to ingest {config['name']}: {str(e)}"
                results['errors'].append(error_msg)
                logger.error(error_msg)
                results['success'] = False
        
        return results
    
    def ingest_dataset(self, config: Dict) -> Dict[str, any]:
        """Ingest a single dataset"""
        file_path = self.datasets_dir / config['file']
        
        # Step 1: Dataset Discovery
        if not file_path.exists():
            raise FileNotFoundError(f"Dataset file not found: {file_path}")
        
        # Step 2: Schema Validation
        df = pd.read_csv(file_path)
        self._validate_schema(df, config['schema'])
        
        # Step 3: Data Loading
        df = self._load_data(df, config['schema'])
        
        # Step 4: Data Cleaning
        df = self._clean_data(df, config['name'])
        
        # Step 5: Data Transformation
        df = self._transform_data(df, config['table'])
        
        # Step 6: Data Quality Checks
        quality_report = self._check_data_quality(df, config['name'])
        
        # Step 7: Database Insertion
        records_inserted = self._insert_to_database(df, config['table'])
        
        # Step 8: Metadata Storage
        self._store_metadata(config, records_inserted, quality_report)
        
        return {
            'success': True,
            'records_inserted': records_inserted,
            'quality_report': quality_report
        }
    
    def _validate_schema(self, df: pd.DataFrame, schema: Dict) -> None:
        """Validate dataset schema"""
        # Check required columns
        required_columns = schema.get('required_columns', [])
        missing_columns = set(required_columns) - set(df.columns)
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        # Check data types
        for col, expected_type in schema.get('column_types', {}).items():
            if col in df.columns:
                if not self._check_dtype(df[col], expected_type):
                    raise ValueError(f"Column {col} has incorrect data type")
        
        # Check value ranges
        for col, range_config in schema.get('value_ranges', {}).items():
            if col in df.columns:
                self._check_value_range(df[col], range_config, col)
    
    def _check_dtype(self, series: pd.Series, expected_type: str) -> bool:
        """Check if series matches expected data type"""
        type_mapping = {
            'int': ['int64', 'int32'],
            'float': ['float64', 'float32'],
            'string': ['object', 'string'],
            'date': ['datetime64[ns]']
        }
        
        actual_type = str(series.dtype)
        return any(t in actual_type for t in type_mapping.get(expected_type, []))
    
    def _check_value_range(self, series: pd.Series, range_config: Dict, col_name: str) -> None:
        """Check if values are within valid range"""
        min_val = range_config.get('min')
        max_val = range_config.get('max')
        
        if min_val is not None:
            if series.min() < min_val:
                raise ValueError(f"Column {col_name} has values below minimum: {series.min()}")
        
        if max_val is not None:
            if series.max() > max_val:
                raise ValueError(f"Column {col_name} has values above maximum: {series.max()}")
    
    def _load_data(self, df: pd.DataFrame, schema: Dict) -> pd.DataFrame:
        """Load and parse data"""
        # Parse date columns
        date_columns = schema.get('date_columns', [])
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # Handle missing values
        for col in df.columns:
            if df[col].isnull().sum() > 0:
                missing_threshold = schema.get('missing_threshold', 0.3)
                missing_ratio = df[col].isnull().sum() / len(df)
                if missing_ratio > missing_threshold:
                    logger.warning(f"Column {col} has {missing_ratio:.2%} missing values")
        
        return df
    
    def _clean_data(self, df: pd.DataFrame, dataset_name: str) -> pd.DataFrame:
        """Clean data"""
        # Remove duplicates
        initial_count = len(df)
        df = df.drop_duplicates()
        duplicates_removed = initial_count - len(df)
        
        if duplicates_removed > 0:
            logger.info(f"Removed {duplicates_removed} duplicate records from {dataset_name}")
        
        # Standardize text columns
        text_columns = df.select_dtypes(include=['object']).columns
        for col in text_columns:
            df[col] = df[col].str.strip().str.title()
        
        return df
    
    def _transform_data(self, df: pd.DataFrame, table_name: str) -> pd.DataFrame:
        """Transform data to match database schema"""
        # Column mapping
        column_mapping = {
            'crops': {
                'crop_id': 'id',
                'name': 'name',
                'scientific_name': 'scientific_name',
                'category': 'category',
                'growing_season': 'growing_season',
                'duration_days': 'duration_days'
            },
            'crop_growth_stages': {
                'stage_id': 'id',
                'crop_id': 'crop_id',
                'stage_name': 'stage_name',
                'stage_order': 'stage_order',
                'duration_days': 'duration_days',
                'kc_value': 'kc_value',
                'description': 'description'
            }
        }
        
        if table_name in column_mapping:
            df = df.rename(columns=column_mapping[table_name])
        
        # Add timestamps
        df['created_at'] = datetime.now()
        
        return df
    
    def _check_data_quality(self, df: pd.DataFrame, dataset_name: str) -> Dict:
        """Check data quality"""
        quality_report = {
            'total_records': len(df),
            'completeness': {},
            'outliers': {},
            'overall_score': 0.0
        }
        
        # Completeness check
        for col in df.columns:
            completeness = (df[col].notna().sum() / len(df)) * 100
            quality_report['completeness'][col] = completeness
        
        # Outlier check (numerical columns)
        numerical_cols = df.select_dtypes(include=[np.number]).columns
        for col in numerical_cols:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            outliers = df[(df[col] < Q1 - 1.5 * IQR) | (df[col] > Q3 + 1.5 * IQR)]
            quality_report['outliers'][col] = len(outliers)
        
        # Calculate overall quality score
        avg_completeness = np.mean(list(quality_report['completeness'].values()))
        total_outliers = sum(quality_report['outliers'].values())
        outlier_penalty = min(total_outliers / len(df) * 10, 20)
        quality_report['overall_score'] = avg_completeness - outlier_penalty
        
        return quality_report
    
    def _insert_to_database(self, df: pd.DataFrame, table_name: str) -> int:
        """Insert data into database"""
        try:
            # Use if_exists='replace' for initial load, 'append' for updates
            records_inserted = df.to_sql(
                table_name,
                self.engine,
                if_exists='append',
                index=False
            )
            return len(df)
        except SQLAlchemyError as e:
            self.engine.rollback()
            raise Exception(f"Database insertion failed: {str(e)}")
    
    def _store_metadata(self, config: Dict, records_inserted: int, quality_report: Dict) -> None:
        """Store ingestion metadata"""
        metadata = {
            'dataset_name': config['name'],
            'file_path': str(self.datasets_dir / config['file']),
            'table_name': config['table'],
            'ingestion_timestamp': datetime.now().isoformat(),
            'records_inserted': records_inserted,
            'quality_report': quality_report
        }
        
        self.ingestion_log.append(metadata)
        logger.info(f"Metadata stored for {config['name']}")
    
    # Schema definitions
    def _get_crop_schema(self) -> Dict:
        return {
            'required_columns': ['crop_id', 'name', 'category', 'growing_season', 'duration_days'],
            'column_types': {
                'crop_id': 'int',
                'name': 'string',
                'scientific_name': 'string',
                'category': 'string',
                'growing_season': 'string',
                'duration_days': 'int'
            },
            'value_ranges': {
                'duration_days': {'min': 1, 'max': 365}
            }
        }
    
    def _get_variety_schema(self) -> Dict:
        return {
            'required_columns': ['variety_id', 'crop_id', 'name'],
            'column_types': {
                'variety_id': 'int',
                'crop_id': 'int',
                'name': 'string'
            }
        }
    
    def _get_growth_stage_schema(self) -> Dict:
        return {
            'required_columns': ['stage_id', 'crop_id', 'stage_name', 'stage_order', 'kc_value'],
            'column_types': {
                'stage_id': 'int',
                'crop_id': 'int',
                'stage_name': 'string',
                'stage_order': 'int',
                'kc_value': 'float'
            },
            'value_ranges': {
                'kc_value': {'min': 0.5, 'max': 1.5}
            }
        }
    
    def _get_soil_schema(self) -> Dict:
        return {
            'required_columns': ['soil_id', 'state', 'district', 'ph_avg'],
            'column_types': {
                'soil_id': 'int',
                'state': 'string',
                'district': 'string',
                'ph_avg': 'float'
            },
            'value_ranges': {
                'ph_avg': {'min': 0, 'max': 14}
            }
        }
    
    def _get_weather_schema(self) -> Dict:
        return {
            'required_columns': ['weather_id', 'district', 'date', 'temperature_avg'],
            'column_types': {
                'weather_id': 'int',
                'district': 'string',
                'date': 'date',
                'temperature_avg': 'float'
            },
            'date_columns': ['date'],
            'value_ranges': {
                'temperature_avg': {'min': -50, 'max': 60},
                'humidity': {'min': 0, 'max': 100}
            }
        }
    
    def _get_rainfall_schema(self) -> Dict:
        return {
            'required_columns': ['rainfall_id', 'district', 'date', 'daily_rainfall'],
            'column_types': {
                'rainfall_id': 'int',
                'district': 'string',
                'date': 'date',
                'daily_rainfall': 'float'
            },
            'date_columns': ['date'],
            'value_ranges': {
                'daily_rainfall': {'min': 0, 'max': 500}
            }
        }


def main():
    import os
    
    # Get database URL from environment
    db_url = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost:5432/cwr_db')
    
    # Initialize ingestion service
    service = DatasetIngestionService(db_url=db_url)
    
    # Ingest all datasets
    results = service.ingest_all_datasets()
    
    # Print results
    print("\n=== Dataset Ingestion Results ===")
    print(f"Overall Success: {results['success']}")
    print(f"\nDatasets Processed:")
    for name, result in results['datasets'].items():
        print(f"  {name}: {result['records_inserted']} records inserted")
    
    if results['errors']:
        print(f"\nErrors:")
        for error in results['errors']:
            print(f"  - {error}")


if __name__ == "__main__":
    main()
```

---

## Dataset Update Mechanism

### Incremental Updates

```python
def ingest_dataset_incremental(self, config: Dict) -> Dict[str, any]:
    """Ingest dataset with incremental updates"""
    file_path = self.datasets_dir / config['file']
    
    # Load new data
    df_new = pd.read_csv(file_path)
    
    # Load existing data from database
    df_existing = pd.read_sql(
        f"SELECT * FROM {config['table']}",
        self.engine
    )
    
    # Identify new records
    id_column = config['schema'].get('id_column', 'id')
    existing_ids = set(df_existing[id_column].values)
    new_records = df_new[~df_new[id_column].isin(existing_ids)]
    
    # Identify updated records
    updated_records = df_new[df_new[id_column].isin(existing_ids)]
    
    # Insert new records
    if not new_records.empty:
        self._insert_to_database(new_records, config['table'])
    
    # Update existing records
    if not updated_records.empty:
        self._update_database(updated_records, config['table'], id_column)
    
    return {
        'new_records': len(new_records),
        'updated_records': len(updated_records)
    }
```

---

## Data Quality Monitoring

### Quality Dashboard

```python
def generate_quality_dashboard(self) -> Dict:
    """Generate data quality dashboard"""
    dashboard = {
        'datasets': {},
        'overall_health': 0.0
    }
    
    tables = ['crops', 'crop_growth_stages', 'district_soil_map', 'weather_data']
    
    for table in tables:
        df = pd.read_sql(f"SELECT * FROM {table}", self.engine)
        
        table_health = {
            'total_records': len(df),
            'completeness': {},
            'duplicate_count': df.duplicated().sum(),
            'health_score': 0.0
        }
        
        # Calculate completeness per column
        for col in df.columns:
            completeness = (df[col].notna().sum() / len(df)) * 100
            table_health['completeness'][col] = completeness
        
        # Calculate health score
        avg_completeness = np.mean(list(table_health['completeness'].values()))
        duplicate_penalty = (table_health['duplicate_count'] / len(df)) * 10
        table_health['health_score'] = avg_completeness - duplicate_penalty
        
        dashboard['datasets'][table] = table_health
    
    # Calculate overall health
    all_scores = [v['health_score'] for v in dashboard['datasets'].values()]
    dashboard['overall_health'] = np.mean(all_scores)
    
    return dashboard
```

---

## Dataset Versioning

### Version Control

```python
def create_dataset_version(self, dataset_name: str) -> str:
    """Create a versioned copy of the dataset"""
    version = datetime.now().strftime("%Y%m%d_%H%M%S")
    versioned_table = f"{dataset_name}_{version}"
    
    # Create versioned table
    df = pd.read_sql(f"SELECT * FROM {dataset_name}", self.engine)
    df.to_sql(versioned_table, self.engine, if_exists='replace', index=False)
    
    # Log version
    version_log = {
        'dataset_name': dataset_name,
        'version': version,
        'versioned_table': versioned_table,
        'created_at': datetime.now().isoformat(),
        'record_count': len(df)
    }
    
    # Store version log in metadata table
    # (Implementation depends on metadata table structure)
    
    return version
```

---

## Error Handling & Recovery

### Error Recovery Strategy

```python
def ingest_with_recovery(self, config: Dict) -> Dict[str, any]:
    """Ingest dataset with error recovery"""
    try:
        # Attempt ingestion
        result = self.ingest_dataset(config)
        return result
    except Exception as e:
        logger.error(f"Ingestion failed for {config['name']}: {str(e)}")
        
        # Attempt recovery
        recovery_result = self._attempt_recovery(config, e)
        
        if recovery_result['success']:
            logger.info(f"Recovery successful for {config['name']}")
            return recovery_result
        else:
            # Log failure for manual intervention
            self._log_failure(config, e)
            raise

def _attempt_recovery(self, config: Dict, error: Exception) -> Dict:
    """Attempt to recover from ingestion error"""
    # Recovery strategies based on error type
    if "duplicate" in str(error).lower():
        # Handle duplicates by skipping
        return self._ingest_skip_duplicates(config)
    elif "constraint" in str(error).lower():
        # Handle constraint violations
        return self._ingest_skip_violations(config)
    else:
        return {'success': False}
```

---

## Ingestion Scheduling

### Automated Scheduling

```python
# Using APScheduler for automated ingestion
from apscheduler.schedulers.blocking import BlockingScheduler

def schedule_ingestion():
    """Schedule periodic dataset ingestion"""
    scheduler = BlockingScheduler()
    
    # Schedule daily ingestion at 2 AM
    scheduler.add_job(
        ingest_all_datasets,
        'cron',
        hour=2,
        minute=0,
        id='daily_ingestion'
    )
    
    # Schedule weekly quality check
    scheduler.add_job(
        generate_quality_dashboard,
        'cron',
        day_of_week='mon',
        hour=3,
        minute=0,
        id='weekly_quality_check'
    )
    
    scheduler.start()
```

---

## Key Design Decisions

### 1. Separate Dataset Directory
- **Reason**: Easy dataset management, version control
- **Implementation**: `/datasets` directory with subdirectories by category

### 2. Schema-Based Validation
- **Reason**: Ensure data quality before database insertion
- **Implementation**: Schema definitions with validation rules

### 3. Batch Insertion
- **Reason**: Performance optimization for large datasets
- **Implementation**: Pandas `to_sql` with batch operations

### 4. Quality Reporting
- **Reason**: Monitor data health, identify issues
- **Implementation**: Completeness, outlier, and health score metrics

### 5. Incremental Updates
- **Reason**: Efficient updates without full reload
- **Implementation**: ID-based comparison for new/updated records

### 6. Versioning
- **Reason**: Reproducibility, rollback capability
- **Implementation**: Timestamped table copies

### 7. Error Recovery
- **Reason**: Robust ingestion, minimize manual intervention
- **Implementation**: Automatic recovery strategies for common errors

### 8. Metadata Logging
- **Reason**: Audit trail, debugging support
- **Implementation**: Ingestion log with timestamps and record counts
