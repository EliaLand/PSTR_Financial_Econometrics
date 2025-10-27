# \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
# WORLD BANK MODULE
# \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\

# Requirements setup 
# We import from config_API the API key for the call to the provider's server
import pandas as pd
import wbgapi as wb

def fetch_worldbank_data(indicator: str, countries: list = ["US"], start=2000, end=2025) -> pd.DataFrame:
    """
    Fetch indicator data from the World Bank API.
    
    Args:
        indicator: Indicator code (e.g. 'NY.GDP.MKTP.CD')
        countries: List of country ISO codes (default: ['US'])
        start: Start year
        end: End year
    
    Returns:
        DataFrame with columns ['country', 'year', indicator].
    """
    data = wb.data.DataFrame(indicator, countries, time=range(start, end + 1))
    data = data.reset_index().rename(columns={"economy": "country", "time": "year"})
    return data
