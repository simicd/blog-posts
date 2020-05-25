# To add a new cell, type '# %%'
# To add a new markdown cell, type '# %% [markdown]'
# %% [markdown]
# # Download files - EIOPA rates
# %% [markdown]
# ## Setup

# %%
import os
import datetime
from dateutil.relativedelta import relativedelta
import requests
from zipfile import ZipFile
from io import BytesIO


# %%
# EIOPA rates go back to 2016 - no prior dates are available
years = [2019, 2018, 2017, 2016]

raw_data_path = r'../datasets/eiopa/raw'
clean_data_path = r'../datasets/eiopa/clean'


# %%
# Create folders if they don't exist
os.makedirs(raw_data_path, exist_ok=True)
os.makedirs(clean_data_path, exist_ok=True)

# %% [markdown]
# ## Turn into month-end date list

# %%
# Get all month-end dates for the years specified above
dates = []
for year in years:
    for month in range(1, 12 + 1):
        # relativedelta() adds up to the last day in the month
        dates.append(datetime.date(year, month, 1) + relativedelta(day=31))
dates[:5]

# %% [markdown]
# ## Generate links

# %%
def generate_eiopa_rfr_url(date: datetime.date):
    base_url= r'https://www.eiopa.europa.eu/sites/default/files/risk_free_interest_rate'
    return f"{base_url}/eiopa_rfr_{str(date).replace('-', '')}.zip"


# %%
url_dict = {}
for date in dates:
    url_dict[str(date)] = generate_eiopa_rfr_url(date)

# Display first link in dictionary (dates are the keys)
url_dict[list(url_dict.keys())[0]]

# %% [markdown]
# ## Define download & unzip functions

# %%
def download_content(url: str):
    """Submit response to server and return response content if successful"""

    response = requests.get(url)
    if response.ok:
        return response.content
    else:
        return None


def store_file(file_object, filepath: str):
    """Store file at target location specified in filepath variable"""

    with open(filepath, 'wb') as file:
        file.write(file_object)


def unzip(file_object, filepath: str):
    """Unzip file and store content at target location specified in filepath variable"""

    # ZipFile class expects a file location, e.g. ZipFile("file.zip","r") or a virtual file (BytesIO)
    with ZipFile(file_object) as zip_file:
        zip_file.extractall(filepath)

# %% [markdown]
# ## Download and unzip

# %%
for date, url in url_dict.items():
    try:
        # Get zipped file content from web
        web_content = download_content(url)

        # Since we get the file directly from the web, it's passed into BytesIO and turned into a virtual file
        file_object = BytesIO(web_content)

        # Unzip it into current location with subfolder
        unzip(file_object, filepath=os.path.join(raw_data_path, 'EIOPA-RFR', f'{date}'))
    except:
        print(f"Download of {date} not successful")

