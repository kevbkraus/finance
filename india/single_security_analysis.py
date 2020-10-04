# single_security_analysis.py ---------------------------------------------------------------------------
# Description:
#   1. Examines the data for missing values and informs user if there are too many missing values 
#   2. Produces data and visuals for EDA of a given security
#   3. Compares the security with the market's risk, creates visuals pertaining to the same
#   4. Appends useful data resulting from all the above analysis to the raw data and stores the result
#      in a new csv file
# -------------------------------------------------------------------------------------------------------

# Libraries
import math
import numpy as np
import numpy.linalg as la
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

import calendar
import sys
import errno

# Get input from user for the file that has NSE price data of the security in question
security_prices_file = input('Enter NSE compiled prices file (full path): ')

# Preprocessing
raw_data = pd.read_csv(security_prices_file)

print(raw_data.head())  # Display few rows just so that user can see if there is anything unusual

old_colnames = list(raw_data.columns)   # Change column names to remove the annoying '<', '>'
new_colnames = [name[1:-1] for name in old_colnames]
raw_data.columns = new_colnames

refined_data = raw_data.sort_values(by='date')    # Sort data according to date and drop duplicates
refined_data.drop_duplicates(inplace+True)

dates = pd.to_datetime(refined_data['<date>'], format="%Y%m%d") # Extract year, month names and weekday names
years = [item.year for item in dates]                           # and add new columns for these in the refined
months = [item.months for item in dates]                        # data. This will be very useful later when we
weekdays = [item.weekday() for item in dates]                   # create plots
weekdays_name = [calendar.day_name[day] for day in weekdays]
months_name = [calendar.month_name[month] for month in months]

refined_data.assign(year = years)
refined_data.assign(month = months_name)
refined_data.assign(day = weekdays_name)




