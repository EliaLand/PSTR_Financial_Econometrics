# \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
# USITC MODULE (US import data combined)
# \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\

# Requirements setup 
import glob
import os 
import re
import pandas as pd

# Paths for saving 
# We import raw .xlsx dfs from  USITC statistic bureau to then tranform them in more friendly .csv dfs
XLSX_DIR = "data_fetcher/raw_df/US_import_data_raw/US_trade_import_data_xlsx"            
CSV_DIR  = "data_fetcher/raw_df/US_import_data_raw/US_trade_import_data_csv"         
OUT_FILE = "data_fetcher/raw_df/US_import_USITC_raw.csv"

# Check existence of the directory 
# Convert each Excel -> CSV (drop "Total:" rows)
os.makedirs(CSV_DIR, exist_ok=True)
xlsx_files = glob.glob(os.path.join(XLSX_DIR, "*.xlsx"))

#____________________________________________________________________________________________________
# Helper functions for cleaning the df
#____________________________________________________________________________________________________

# Country name cleaning 
def clean_country_name_from_df(df):
    if "Country" in df.columns:
        vals = df["Country"].dropna().unique()
        if len(vals) > 0:
            return str(vals[0]).strip()
    return None

# Drop useless footer rows  
def drop_total_rows(df):
    first_col = df.columns[0]
    mask_total = df[first_col].astype(str).str.fullmatch(r"\s*Total:\s*", case=False, na=False)

# If all the key columns are NaN for one row, drop the row
    key_cols = [c for c in ["Country","Year","Month","HTS Number","Description"] if c in df.columns]
    if key_cols:
        mask_empty_keys = df[key_cols].isna().all(axis=1)
        return df.loc[~(mask_total | mask_empty_keys)].copy()
    return df.loc[~mask_total].copy()

#____________________________________________________________________________________________________

# Files restructuring 
# Troubleshooting try format deactivated
# (!!!) Read second sheet only (index=1)

for file in xlsx_files:
    df = pd.read_excel(file, sheet_name=1, engine="openpyxl", dtype=str)
    df.columns = df.columns.str.strip()

# Recall drop_total_rows (df)
    df = drop_total_rows(df)

# Whitespace normalization in columns of string type
    for column in df.select_dtypes(include="object").columns:
        df[column] = df[column].str.strip()

# Rename file name per each country 
# Just easier to search instead of going for the query call id
    country = clean_country_name_from_df(df)
    if country is None:
        base = os.path.splitext(os.path.basename(file))[0]
        country = re.sub(r"[^A-Za-z]+", "_", base) or "Unknown"

# Convert to CSV
# (!!!) Make sure the csv is in comma separated format and not EU format
    out_csv = os.path.join(CSV_DIR, f"{country}.csv")
    df.to_csv(out_csv, index=False, sep=",", decimal=".")

# Aggregated df.csv only for US import data
# (!!!) This process dows not apply to export data as they are already displayed in aggregated format
csv_files = glob.glob(os.path.join(CSV_DIR, "*.csv"))
parts = []
for file in csv_files:
    parts.append(pd.read_csv(file, sep=",", decimal=".", dtype=str))

US_import_USITC_raw_df = pd.concat(parts, ignore_index=True)
US_import_USITC_raw_df.to_csv(OUT_FILE, index=False, sep=",", decimal=".")