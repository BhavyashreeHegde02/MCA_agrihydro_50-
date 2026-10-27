# %% [markdown]
# # Data Integration and Curation Pipeline
# This notebook generates the canonical datasets and curated views for the Jalachakra agricultural hydrology project.
# It ensures data integrity, preserves source lineage, and documents transformations.

# %% [markdown]
# ### Section 1: Setup & Configuration

# %%
import pandas as pd
import numpy as np
from pathlib import Path
import os
import warnings

warnings.filterwarnings('ignore')

# Determine project root dynamically
try:
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
except NameError:
    # Fallback for interactive execution
    PROJECT_ROOT = Path(os.getcwd())
    if PROJECT_ROOT.name == "notebooks":
        PROJECT_ROOT = PROJECT_ROOT.parent

DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
CLEANED_DIR = DATA_DIR / "cleaned"
CURATED_DIR = DATA_DIR / "curated"

# Create curated directory if it doesn't exist
CURATED_DIR.mkdir(parents=True, exist_ok=True)

print(f"Project Root: {PROJECT_ROOT}")
print(f"Curated Output Directory: {CURATED_DIR}")

# %% [markdown]
# ### Section 2: Load Cleaned Data

# %%
# Load Cleaned Data
crop_cleaned = pd.read_csv(CLEANED_DIR / "crop_data_cleaned.csv")
rainfall_cleaned = pd.read_csv(CLEANED_DIR / "rainfall_cleaned.csv")
soil_cleaned = pd.read_csv(CLEANED_DIR / "soil_cleaned.csv")
climate_cleaned = pd.read_csv(CLEANED_DIR / "climate_cleaned.csv")

# Load Raw Reference Data
fao_kc_raw = pd.read_csv(RAW_DIR / "fao_crop_kc.csv")
district_codes_raw = pd.read_csv(RAW_DIR / "karnataka_district_codes.csv")

print("Data Loaded Successfully.")
print(f"Crop Data: {crop_cleaned.shape}")
print(f"Rainfall Data: {rainfall_cleaned.shape}")
print(f"Soil Data: {soil_cleaned.shape}")
print(f"Climate Data: {climate_cleaned.shape}")
print(f"FAO Kc Reference: {fao_kc_raw.shape}")
print(f"District Codes Reference: {district_codes_raw.shape}")

# %% [markdown]
# ### Section 3: Canonical Crop Mapping

# %%
# Canonical mapping definition
crop_mappings = [
    ("Rice", "rice", "cereal", "lowercase normalization"),
    ("Paddy", "rice", "cereal", "paddy is unhusked rice"),
    ("Maize", "maize", "cereal", "lowercase normalization"),
    ("Ragi", "finger_millet", "millet", "ragi is common name for finger millet"),
    ("Finger Millet", "finger_millet", "millet", "lowercase_underscore normalization"),
    ("Jowar", "sorghum", "millet", "jowar is common name for sorghum"),
    ("Bajra", "pearl_millet", "millet", "bajra is common name for pearl millet"),
    ("Wheat", "wheat", "cereal", "lowercase normalization"),
    ("Small Millets", "small_millets", "millet", "lowercase_underscore normalization"),
    ("Soyabean", "soybean", "oilseed", "spelling variant normalization"),
    ("Groundnut", "groundnut", "oilseed", "lowercase normalization"),
    ("Sunflower", "sunflower", "oilseed", "lowercase normalization"),
    ("Sesamum", "sesamum", "oilseed", "lowercase normalization"),
    ("Linseed", "linseed", "oilseed", "lowercase normalization"),
    ("Castor seed", "castor_seed", "oilseed", "lowercase_underscore normalization"),
    ("Niger seed", "niger_seed", "oilseed", "lowercase_underscore normalization"),
    ("Cotton(lint)", "cotton", "fibre", "name variant, lint qualifier removed"),
    ("Sugarcane", "sugarcane", "sugar", "lowercase normalization"),
    ("Tobacco", "tobacco", "commercial", "lowercase normalization"),
    ("Coffee", "coffee", "plantation", "lowercase normalization"),
    ("Coconut", "coconut", "plantation", "lowercase normalization"),
    ("Arecanut", "arecanut", "plantation", "lowercase normalization"),
    ("Cashewnut", "cashewnut", "plantation", "lowercase normalization"),
    ("Black pepper", "black_pepper", "spice", "lowercase_underscore normalization"),
    ("Cardamom", "cardamom", "spice", "lowercase normalization"),
    ("Coriander", "coriander", "spice", "lowercase normalization"),
    ("Chillies (Green)", "chilli", "spice", "name variant normalization"),
    ("Tur (Arhar)", "tur", "pulse", "name variant, parenthetical removed"),
    ("Moong(Green Gram)", "moong", "pulse", "name variant, parenthetical removed"),
    ("Urad", "urad", "pulse", "lowercase normalization"),
    ("Masoor", "masoor", "pulse", "lowercase normalization"),
    ("Horse Gram", "horse_gram", "pulse", "lowercase_underscore normalization"),
    ("Moth", "moth", "pulse", "lowercase normalization"),
    ("Other Kharif pulses", "other_kharif_pulses", "pulse", "lowercase_underscore normalization"),
    ("Other Rabi pulses", "other_rabi_pulses", "pulse", "lowercase_underscore normalization"),
    ("Peas & beans (Pulses)", "peas_and_beans", "pulse", "name normalization"),
    ("Potato", "potato", "vegetable", "lowercase normalization"),
    ("Tomato", "tomato", "vegetable", "lowercase normalization"),
    ("Onion", "onion", "vegetable", "lowercase normalization"),
    ("Sweet potato", "sweet_potato", "vegetable", "lowercase_underscore normalization"),
    ("Tapioca", "tapioca", "tuber", "lowercase normalization"),
    ("Banana", "banana", "fruit", "lowercase normalization"),
    ("Mango", "mango", "fruit", "lowercase normalization"),
    ("Grapes", "grapes", "fruit", "lowercase normalization")
]

canonical_crop_mapping = pd.DataFrame(crop_mappings, columns=["original_crop_name", "canonical_crop_name", "crop_category", "mapping_reason"])
canonical_crop_mapping["mapping_source"] = "jalachakra_canonical_v1"

print(f"Created canonical crop mapping with {len(canonical_crop_mapping)} entries.")

# %% [markdown]
# ### Section 4: Canonical Location Mapping

# %%
# Canonical location mapping definition
locations = []
for idx, row in district_codes_raw.iterrows():
    locations.append({
        "original_state": "Karnataka", # Handle mixed case in raw data later by mapping to UPPER
        "canonical_state": "KARNATAKA",
        "original_district": row['District_Name'],
        "canonical_district": row['District_Name'], # Already uppercase
        "district_code": row['District_Code'],
        "state_code": row['State_Code'],
        "mapping_status": "VERIFIED",
        "mapping_source": "karnataka_district_codes_reference"
    })

canonical_location_mapping = pd.DataFrame(locations)
print(f"Created canonical location mapping with {len(canonical_location_mapping)} district entries.")

# %% [markdown]
# ### Section 5: Build crop_location_evidence.csv

# %%
# Build evidence base
# First merge canonical maps
crop_loc_df = crop_cleaned.copy()
crop_loc_df['source_row_id'] = crop_loc_df.index

# Join with location mapping (case insensitive match on district)
crop_loc_df['District_Upper'] = crop_loc_df['District_Name'].str.upper()
loc_map_lookup = canonical_location_mapping.set_index('canonical_district')['district_code'].to_dict()
crop_loc_df['district_code'] = crop_loc_df['District_Upper'].map(loc_map_lookup)

# Join with crop mapping
crop_map_lookup = canonical_crop_mapping.set_index('original_crop_name')[['canonical_crop_name', 'crop_category']].to_dict('index')
crop_loc_df['canonical_crop'] = crop_loc_df['Crop'].map(lambda x: crop_map_lookup.get(x, {}).get('canonical_crop_name'))
crop_loc_df['crop_category'] = crop_loc_df['Crop'].map(lambda x: crop_map_lookup.get(x, {}).get('crop_category'))

evidence_df = pd.DataFrame({
    'state': crop_loc_df['State_Name'],
    'district': crop_loc_df['District_Name'],
    'district_code': crop_loc_df['district_code'],
    'year': crop_loc_df['Crop_Year'],
    'crop': crop_loc_df['Crop'],
    'canonical_crop': crop_loc_df['canonical_crop'],
    'crop_category': crop_loc_df['crop_category'],
    'area': crop_loc_df['Area'],
    'production': crop_loc_df['Production'],
    'yield': crop_loc_df['Yield'],
    'season': crop_loc_df['Season'],
    'evidence_type': 'HISTORICAL_PRODUCTION',
    'source_dataset': 'karnataka_crop_data',
    'source_row_id': crop_loc_df['source_row_id']
})

print(f"Crop location evidence built: {len(evidence_df)} rows.")

# %% [markdown]
# ### Section 6: Build crop_reference_catalog.csv

# %%
# Build crop reference catalog
fao_map = {
    "Rice": "rice", "Wheat": "wheat", "Maize": "maize", "Soybean": "soybean", 
    "Cotton": "cotton", "Sugarcane": "sugarcane", "Groundnut": "groundnut", 
    "Sunflower": "sunflower", "Sorghum": "sorghum", "Pearl Millet": "pearl_millet", 
    "Finger Millet": "finger_millet", "Tur/Pigeon Pea": "tur", "Tobacco": "tobacco", 
    "Potato": "potato", "Tomato": "tomato", "Onion": "onion", "Chilli": "chilli"
}

fao_df = fao_kc_raw.copy()
fao_df['canonical_crop'] = fao_df['Crop'].map(fao_map)

# Fetch categories from canonical mapping
category_lookup = canonical_crop_mapping.set_index('canonical_crop_name')['crop_category'].to_dict()
fao_df['crop_category'] = fao_df['canonical_crop'].map(category_lookup)

ref_catalog_rows = []

# Process FAO crops
for idx, row in fao_df.iterrows():
    ref_catalog_rows.append({
        'crop': row['Crop'],
        'canonical_crop': row['canonical_crop'],
        'crop_category': row['crop_category'],
        'growth_stage': row['Stage'],
        'kc': row['Kc'],
        'duration_days': row['Duration_Days'],
        'source': 'FAO-56',
        'reference_type': 'STANDARD_REFERENCE',
        'cwr_support_status': 'REFERENCE_ONLY'
    })

ref_catalog = pd.DataFrame(ref_catalog_rows)

# Add crops that are in production but NOT in FAO
prod_canonical_crops = evidence_df['canonical_crop'].dropna().unique()
fao_canonical_crops = ref_catalog['canonical_crop'].dropna().unique()

missing_crops = set(prod_canonical_crops) - set(fao_canonical_crops)

missing_rows = []
for c in missing_crops:
    cat = category_lookup.get(c, "unknown")
    missing_rows.append({
        'crop': canonical_crop_mapping[canonical_crop_mapping['canonical_crop_name'] == c]['original_crop_name'].iloc[0],
        'canonical_crop': c,
        'crop_category': cat,
        'growth_stage': np.nan,
        'kc': np.nan,
        'duration_days': np.nan,
        'source': np.nan,
        'reference_type': 'NO_REFERENCE',
        'cwr_support_status': 'REFERENCE_ONLY'
    })

ref_catalog = pd.concat([ref_catalog, pd.DataFrame(missing_rows)], ignore_index=True)
print(f"Crop reference catalog built: {len(ref_catalog)} rows.")

# %% [markdown]
# ### Section 7: Build soil_context_reference.csv

# %%
# Soil context reference
soil_ctx = soil_cleaned.copy()
soil_ctx['source_row_id'] = soil_ctx.index

soil_context = pd.DataFrame({
    'state_if_verified': 'KARNATAKA',
    'district': soil_ctx['District_Name'],
    'nitrogen': soil_ctx['N'],
    'phosphorus': soil_ctx['P'],
    'potassium': soil_ctx['K'],
    'ph': soil_ctx['pH'],
    'ec': soil_ctx['EC'],
    'oc': soil_ctx['OC'],
    'sulphur': soil_ctx['S'],
    'zinc': soil_ctx['Zn'],
    'iron': soil_ctx['Fe'],
    'copper': soil_ctx['Cu'],
    'manganese': soil_ctx['Mn'],
    'boron': soil_ctx['B'],
    'data_status': 'PROVISIONAL',
    'source_dataset': 'soil_karnataka',
    'source_row_id': soil_ctx['source_row_id']
})
print(f"Soil context reference built: {len(soil_context)} rows.")

# %% [markdown]
# ### Section 8: Build rainfall_context.csv

# %%
# Build rainfall context
rainfall_df = rainfall_cleaned.copy()
rainfall_df['source_row_id'] = rainfall_df.index

# Define columns
monthly_cols = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
seasonal_cols = ['Jan-Feb', 'Mar-May', 'Jun-Sep', 'Oct-Dec']
annual_cols = ['ANNUAL']

rain_rows = []
for idx, row in rainfall_df.iterrows():
    base_info = {
        'state': row['STATE'],
        'district': row['DISTRICT'],
        'year': row['YEAR'],
        'source_dataset': 'rainfall_karnataka',
        'source_row_id': row['source_row_id']
    }
    
    # Monthly
    for m in monthly_cols:
        val = row[m]
        rain_rows.append({**base_info, 'period': m, 'rainfall': val, 'period_type': 'MONTHLY', 
                          'quality_flag': 'OBSERVED' if val > 0 else 'ZERO_OR_MISSING'})
    
    # Seasonal
    for s in seasonal_cols:
        val = row[s]
        rain_rows.append({**base_info, 'period': s, 'rainfall': val, 'period_type': 'SEASONAL_AGGREGATE', 
                          'quality_flag': 'OBSERVED' if val > 0 else 'ZERO_OR_MISSING'})
        
    # Annual
    val = row['ANNUAL']
    rain_rows.append({**base_info, 'period': 'ANNUAL', 'rainfall': val, 'period_type': 'ANNUAL', 
                      'quality_flag': 'OBSERVED' if val > 0 else 'ZERO_OR_MISSING'})

rainfall_context = pd.DataFrame(rain_rows)
print(f"Rainfall context built: {len(rainfall_context)} rows.")

# %% [markdown]
# ### Section 9: Build weather_context.csv

# %%
# Weather context
weather_df = climate_cleaned.copy()
weather_df['source_row_id'] = weather_df.index

weather_context = pd.DataFrame({
    'date': weather_df['date'],
    'tavg': weather_df['tavg'],
    'tmin': weather_df['tmin'],
    'tmax': weather_df['tmax'],
    'precipitation': weather_df['prcp'],
    'wind_speed': weather_df['wspd'],
    'pressure': weather_df['pres'],
    'site_id': 'UNKNOWN',
    'location_status': 'UNKNOWN',
    'units_status': 'ASSUMED_METRIC',
    'provenance_status': 'UNVERIFIED',
    'source_dataset': 'climate_raw',
    'source_row_id': weather_df['source_row_id']
})
print(f"Weather context built: {len(weather_context)} rows.")

# %% [markdown]
# ### Section 10: Build application_location_view.csv

# %%
# Aggregate crop location evidence
# Canonical state is always KARNATAKA based on mappings
app_view = evidence_df.groupby(['district', 'district_code', 'season', 'canonical_crop', 'crop_category']).agg(
    years_with_data=('year', 'nunique'),
    avg_area=('area', 'mean'),
    avg_production=('production', 'mean'),
    avg_yield=('yield', 'mean')
).reset_index()

app_view['state'] = 'KARNATAKA'

# Get support status from catalog
support_status_lookup = ref_catalog.drop_duplicates('canonical_crop').set_index('canonical_crop')['cwr_support_status'].to_dict()
app_view['cwr_support_status'] = app_view['canonical_crop'].map(support_status_lookup)
app_view['evidence_type'] = 'REGIONAL_CROP_EVIDENCE'

# Reorder columns as requested
app_view = app_view[['state', 'district', 'district_code', 'season', 'canonical_crop', 'crop_category', 
                     'cwr_support_status', 'years_with_data', 'avg_area', 'avg_production', 'avg_yield', 'evidence_type']]

print(f"Application location view built: {len(app_view)} rows.")

# %% [markdown]
# ### Section 11: Validate Joins

# %%
def validate_join(left_name, right_name, join_key, left_df, right_df, result_df, 
                  join_type, temporal_compat, spatial_compat, unit_compat):
    
    # Simple check for duplication based on left rows vs result rows for a presumed many-to-one mapping
    duplicate_expansion = len(result_df) > len(left_df)
    
    report = {
        'left_dataset': left_name,
        'right_dataset': right_name,  
        'join_key': join_key,
        'left_rows': len(left_df),
        'right_rows': len(right_df),
        'result_rows': len(result_df),
        'cardinality': join_type,
        'duplicate_expansion': duplicate_expansion,
        'expansion_factor': len(result_df) / len(left_df) if len(left_df) > 0 else 0,
        'temporal_compatibility': temporal_compat,
        'spatial_compatibility': spatial_compat,  
        'unit_compatibility': unit_compat,
        'status': 'REJECTED' if duplicate_expansion else 'SAFE'
    }
    return report

join_reports = []

# 1. Crop Data + Canonical Crop Mapping
join_reports.append(validate_join(
    "crop_data", "canonical_crop_mapping", "Crop -> original_crop_name", 
    crop_cleaned, canonical_crop_mapping, evidence_df, "many-to-one", 
    "N/A", "N/A", "N/A"
))

# 2. Crop Data + District Codes
join_reports.append(validate_join(
    "crop_data", "district_codes", "District_Name -> canonical_district", 
    crop_cleaned, canonical_location_mapping, evidence_df, "many-to-one", 
    "N/A", "STATE-LEVEL", "N/A"
))

# 3. Reference Catalog + Canonical Crop Mapping (Implicit via FAO -> Canonical)
join_reports.append(validate_join(
    "fao_kc", "canonical_crop_mapping", "Crop -> FAO map -> canonical_crop_name", 
    fao_kc_raw, canonical_crop_mapping, fao_df, "many-to-one", 
    "N/A", "N/A", "N/A"
))

# 4. Climate Data (No location key)
join_reports.append({
    'left_dataset': 'climate_data', 'right_dataset': 'NONE', 'join_key': 'NONE',
    'left_rows': len(weather_df), 'right_rows': 0, 'result_rows': len(weather_df),
    'cardinality': 'none', 'duplicate_expansion': False, 'expansion_factor': 1.0,
    'temporal_compatibility': 'DAILY', 'spatial_compatibility': 'UNKNOWN', 'unit_compatibility': 'ASSUMED_METRIC',
    'status': 'DOCUMENTED_NO_JOIN_POSSIBLE'
})

# 5. Soil Data (No temporal key)
join_reports.append({
    'left_dataset': 'soil_data', 'right_dataset': 'NONE', 'join_key': 'NONE',
    'left_rows': len(soil_ctx), 'right_rows': 0, 'result_rows': len(soil_ctx),
    'cardinality': 'none', 'duplicate_expansion': False, 'expansion_factor': 1.0,
    'temporal_compatibility': 'NONE', 'spatial_compatibility': 'DISTRICT-LEVEL', 'unit_compatibility': 'STANDARD',
    'status': 'DOCUMENTED_PROVISIONAL'
})

validation_df = pd.DataFrame(join_reports)
print("Join Validations Completed.")
print(validation_df.to_string())

# %% [markdown]
# ### Section 12: Check Duplicate Expansion

# %%
print("Duplicate Expansion Checks:")
for idx, row in validation_df.iterrows():
    print(f"Join: {row['left_dataset']} + {row['right_dataset']} -> Expansion Factor: {row['expansion_factor']:.2f} (Status: {row['status']})")
    if row['duplicate_expansion']:
        print(f"  WARNING: Unexpected duplication in {row['left_dataset']} join.")

# %% [markdown]
# ### Section 13: Check Unmatched Records

# %%
# Crops with no mapping
unmapped_crops = evidence_df[evidence_df['canonical_crop'].isna()]['crop'].unique()
print(f"Crops in production data with no canonical mapping: {len(unmapped_crops)}")
if len(unmapped_crops) > 0:
    print(unmapped_crops)

# Crops in production data with no Kc reference
no_kc = evidence_df[evidence_df['canonical_crop'].isin(missing_crops)]['canonical_crop'].unique()
print(f"Crops in production data with no Kc reference: {len(no_kc)}")

# Districts in crop data not in district codes
unmapped_districts = evidence_df[evidence_df['district_code'].isna()]['district'].unique()
print(f"Districts in crop data not in district codes: {len(unmapped_districts)}")

# Districts in soil data not in crop data
crop_districts = evidence_df['district'].str.upper().unique()
soil_districts = soil_context['district'].str.upper().unique()
soil_only = set(soil_districts) - set(crop_districts)
print(f"Districts in soil data not in crop data: {len(soil_only)}")


# %% [markdown]
# ### Section 14: Export Curated Data

# %%
canonical_crop_mapping.to_csv(CURATED_DIR / "canonical_crop_mapping.csv", index=False)
canonical_location_mapping.to_csv(CURATED_DIR / "canonical_location_mapping.csv", index=False)
evidence_df.to_csv(CURATED_DIR / "crop_location_evidence.csv", index=False)
ref_catalog.to_csv(CURATED_DIR / "crop_reference_catalog.csv", index=False)
soil_context.to_csv(CURATED_DIR / "soil_context_reference.csv", index=False)
rainfall_context.to_csv(CURATED_DIR / "rainfall_context.csv", index=False)
weather_context.to_csv(CURATED_DIR / "weather_context.csv", index=False)
app_view.to_csv(CURATED_DIR / "application_location_view.csv", index=False)
validation_df.to_csv(CURATED_DIR / "join_validation_report.csv", index=False)

print(f"Successfully exported all curated data artifacts to {CURATED_DIR}")

# %% [markdown]
# ### Section 15: Generate Summary Statistics

# %%
outputs = {
    "canonical_crop_mapping": canonical_crop_mapping,
    "canonical_location_mapping": canonical_location_mapping,
    "crop_location_evidence": evidence_df,
    "crop_reference_catalog": ref_catalog,
    "soil_context_reference": soil_context,
    "rainfall_context": rainfall_context,
    "weather_context": weather_context,
    "application_location_view": app_view,
    "join_validation_report": validation_df
}

print("=== Curated Datasets Summary ===")
for name, df in outputs.items():
    print(f"\nDataset: {name}")
    print(f"Rows: {len(df)}, Columns: {len(df.columns)}")
    if not df.empty:
        # Data Completeness %
        completeness = (df.notna().sum() / len(df) * 100).mean()
        print(f"Average Completeness: {completeness:.2f}%")
        
print("\n=== Cross-Reference Coverage ===")
prod_crop_count = len(prod_canonical_crops)
fao_covered = len(prod_canonical_crops) - len(missing_crops)
print(f"Production crops with Kc coverage: {fao_covered} out of {prod_crop_count} ({(fao_covered/prod_crop_count*100):.1f}%)")
