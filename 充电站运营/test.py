import os
import pandas as pd
from pandasai import Agent
from dotenv import load_dotenv # Import load_dotenv

load_dotenv() # Load variables from .env file

# Sample DataFrame
sales_by_country = pd.DataFrame({
    "country": ["United States", "United Kingdom", "France", "Germany", "Italy", "Spain", "Canada", "Australia", "Japan", "China"],
    "sales": [5000, 3200, 2900, 4100, 2300, 2100, 2500, 2600, 4500, 7000]
})

# Check if the key was loaded successfully
if "PANDASAI_API_KEY" not in os.environ or not os.environ["PANDASAI_API_KEY"].startswith("PAI-"):
     print("ERROR: PANDASAI_API_KEY not found or invalid in environment/.env file.")
     exit() # Or handle appropriately

try:
    agent = Agent(sales_by_country)
    response = agent.chat('Which are the top 5 countries by sales?')
    print(response)
except Exception as e:
    print(f"An error occurred: {e}")