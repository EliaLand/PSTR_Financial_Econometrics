import glob, os, re

# === Paths ===
XLSX_DIR = "data"              # where your 28 .xlsx live
CSV_DIR  = "data_csv"          # where we'll write per-file CSVs
OUT_FILE = "US_import_USITC_raw.csv"

os.makedirs(CSV_DIR, exist_ok=True)

# Convert each Excel -> CSV (drop 'Total:' rows)
xlsx_files = glob.glob(os.path.join(XLSX_DIR, "*.xlsx"))
print(f"Found {len(xlsx_files)} Excel files.")

# Chat-GPT Function :
def clean_country_name_from_df(df):
    if "Country" in df.columns:
        vals = df["Country"].dropna().unique()
        if len(vals) > 0:
            return str(vals[0]).strip()
    return None

def drop_total_rows(df):
    # First column is usually "Data Type"; drop any footer rows like "Total:" (any case/spaces)
    first_col = df.columns[0]
    mask_total = df[first_col].astype(str).str.fullmatch(r"\s*Total:\s*", case=False, na=False)
    # Also defensively drop rows where all key identifiers are NaN but a big grand total sits in value column
    key_cols = [c for c in ["Country","Year","Month","HTS Number","Description"] if c in df.columns]
    if key_cols:
        mask_empty_keys = df[key_cols].isna().all(axis=1)
        return df.loc[~(mask_total | mask_empty_keys)].copy()
    return df.loc[~mask_total].copy()

for f in xlsx_files:
    try:
        # Read 2nd sheet only (index=1)
        df = pd.read_excel(f, sheet_name=1, engine="openpyxl", dtype=str)
        df.columns = df.columns.str.strip()

        # Remove 'Total:' footer rows
        df = drop_total_rows(df)

        # Optional: normalize whitespace in string columns
        for c in df.select_dtypes(include="object").columns:
            df[c] = df[c].str.strip()

        # Derive a friendly per-country filename
        country = clean_country_name_from_df(df)
        if country is None:
            # fallback: derive from filename
            base = os.path.splitext(os.path.basename(f))[0]
            country = re.sub(r"[^A-Za-z]+", "_", base) or "Unknown"

        out_csv = os.path.join(CSV_DIR, f"{country}.csv")
        # Save in EU-style: semicolon sep, comma decimal
        df.to_csv(out_csv, index=False, sep=";", decimal=",")
        print(f" Wrote {out_csv} ({len(df):,} rows)")
    except Exception as e:
        print(f" Skipped {os.path.basename(f)}: {e}")

# Aggregate all CSV
csv_files = glob.glob(os.path.join(CSV_DIR, "*.csv"))
parts = []
for f in csv_files:
    try:
        parts.append(pd.read_csv(f, sep=";", decimal=",", dtype=str))
    except Exception as e:
        print(f" Could not read {os.path.basename(f)}: {e}")

combined_df = pd.concat(parts, ignore_index=True)

# Final sanity: ensure no trailing 'Total:' rows survived
first_col = combined_df.columns[0]
combined_df = combined_df[~combined_df[first_col].astype(str).str.fullmatch(r"\s*Total:\s*", case=False, na=False)].copy()

combined_df.to_csv(OUT_FILE, index=False, sep=";", decimal=",")
print(f"\n Combined file saved as: {OUT_FILE}")
print(f"Total rows: {len(combined_df):,}")
print(combined_df.tail(5))











# US-EU Trade Data from USITC DataWeb
# Monthly bilateral flows between each EU member state and the U.S.
# IMPORTS (U.S. imports FROM EU country):
#   Column "General Customs Value" in USD, not seasonally adjusted.
#   This is the customs value on which tariffs apply.
# EXPORTS (U.S. exports TO EU country):
#   Column "FAS Value" in USD.
# Files: US_import_USITC_raw.csv / US_export_USITC_raw.csv
# Format: semicolon-separated, decimal comma.
# Period: 2020-01 to 2025-06
# We output:
#   US_import_raw : [Country, HTS_Code, HTS_Description, Time, Import - General custom value (USD)]
#   US_export_raw : [Country, HTS_Code, HTS_Description, Time, Export - FAS value (USD)]
# We:
# - harmonize EU country names to ISO-2
# - build Time = YYYY-MM
# - sort by Country, HTS_Code, Time
# E how the fuck did you manage to get a clean df directly without cleaning everything ? Is that the HTS that change everything ?


eu_country_map = {
    "Austria": "AT",
    "Belgium": "BE",
    "Bulgaria": "BG",
    "Croatia": "HR",
    "Cyprus": "CY",
    "Czechia (Czech Republic)": "CZ",
    "Czechia": "CZ",
    "Denmark": "DK",
    "Estonia": "EE",
    "Finland": "FI",
    "France": "FR",
    "Germany": "DE",
    "Greece": "GR",
    "Hungary": "HU",
    "Ireland": "IE",
    "Italy": "IT",
    "Latvia": "LV",
    "Lithuania": "LT",
    "Luxembourg": "LU",
    "Malta": "MT",
    "Netherlands": "NL",
    "Poland": "PL",
    "Portugal": "PT",
    "Romania": "RO",
    "Slovakia": "SK",
    "Slovenia": "SI",
    "Spain": "ES",
    "Sweden": "SE",
    "United Kingdom": "UK",
}

# 1. IMPORTS: U.S. imports FROM EU country
US_import_raw = pd.read_csv(
    "US_import_USITC_raw.csv",
    sep=";",
    decimal=",",
    low_memory=False
)

US_import_raw.columns = US_import_raw.columns.str.strip()
# ISO-2 code
US_import_raw["Country"] = US_import_raw["Country"].map(eu_country_map)

# build Time = YYYY-MM
US_import_raw["Year"] = US_import_raw["Year"].astype(int)
US_import_raw["Month"] = US_import_raw["Month"].astype(int)
US_import_raw["Time"] = (
    US_import_raw["Year"].astype(str) + "-" + US_import_raw["Month"].astype(str).str.zfill(2)
)

# rename columns
US_import_raw = US_import_raw.rename(columns={
    "HTS Number": "HTS_Code",
    "Description": "HTS_Description",
    "General Customs Value": "Import - General custom value (USD)"
})

# Make sure HTS code = dtype to prevents float-rounding issues in merges/sorts
US_import_raw["HTS_Code"] = (
    pd.to_numeric(US_import_raw["HTS_Code"], errors="coerce")
    .astype("Int64")
    .astype(str)
)

# SM : Regulerize comma, space and stuff, dont bother the rest I just had issue with the format of the df
val = "Import - General custom value (USD)"
US_import_raw[val] = (
    US_import_raw[val]
    .astype(str)
    .str.replace("\u202f", "", regex=False)
    .str.replace("\xa0",  "", regex=False)
    .str.strip()
)

US_import_raw[val] = (
    US_import_raw[val]
    .str.replace(",", ".", regex=False)
)

US_import_raw[val] = pd.to_numeric(US_import_raw[val], errors="coerce")

US_import_raw = US_import_raw[US_import_raw[val].notna()].copy()

# sort
US_import_raw = (
    US_import_raw
    .sort_values(["Country", "HTS_Code", "Time"])
    .reset_index(drop=True)
)

# EXPORTS: U.S. exports TO EU country
US_export_raw = pd.read_csv(
    "US_export_USITC_raw.csv",
    sep=";",
    decimal=",",
    low_memory=False
)
US_export_raw.columns = US_export_raw.columns.str.strip()

US_export_raw = US_export_raw[US_export_raw["Country"].isin(eu_country_map.keys())].copy()
US_export_raw["Country"] = US_export_raw["Country"].map(eu_country_map)

US_export_raw["Year"] = US_export_raw["Year"].astype(int)
US_export_raw["Month"] = US_export_raw["Month"].astype(int)
US_export_raw["Time"] = (
    US_export_raw["Year"].astype(str) + "-" + US_export_raw["Month"].astype(str).str.zfill(2)
)

US_export_raw = US_export_raw.rename(columns={
    "HTS Number": "HTS_Code",
    "Description": "HTS_Description",
    "FAS Value": "Export - FAS value (USD)"
})

# Harden HTS code dtype to string as well
US_export_raw["HTS_Code"] = (
    pd.to_numeric(US_export_raw["HTS_Code"], errors="coerce")
    .astype("Int64")
    .astype(str)
)

# numeric
US_export_raw["Export - FAS value (USD)"] = (
    US_export_raw["Export - FAS value (USD)"]
    .astype(str)
    .str.replace("\u202f", "", regex=False)
    .str.replace("\xa0",  "", regex=False)
    .str.strip()
    .str.replace(".", "", regex=False)
    .str.replace(",", ".", regex=False)
)
US_export_raw["Export - FAS value (USD)"] = pd.to_numeric(
    US_export_raw["Export - FAS value (USD)"],
    errors="coerce"
)

# Drop empty export rows
US_export_raw = US_export_raw[US_export_raw["Export - FAS value (USD)"].notna()].copy()

US_export_raw = (
    US_export_raw
    .sort_values(["Country", "HTS_Code", "Time"])
    .reset_index(drop=True)
)

# Final preview
US_import_raw.head(), US_export_raw.head()